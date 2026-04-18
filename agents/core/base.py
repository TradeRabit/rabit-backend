"""Base agent class for Claude Agent SDK."""
import base64
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from anthropic import Anthropic, AsyncAnthropic

from agents.backpack_execution import (
    get_backpack_execution_guidance,
    normalize_backpack_execution,
)
from agents.compression import ConversationCompressor
from agents.conversation_style import (
    CONVERSATION_STYLE_NORMAL,
    get_conversation_style_guidance,
    normalize_conversation_style,
)
from agents.openrouter import get_openrouter_session_cost_service
from agents.intent_router import AgentIntentContext, build_intent_prompt, parse_intent_response
from agents.drift_execution import (
    get_drift_execution_guidance,
    normalize_drift_execution,
)
from agents.memory import ConversationMemory, Mem0Error, Message, get_mem0_client
from agents.market_context import get_market_context_guidance, normalize_market_context
from agents.tools import ToolResult, tool_registry
from agents.tools.core.runtime_context import (
    reset_current_backpack_execution,
    reset_current_drift_execution,
    reset_current_event_emitter,
    reset_current_market_context,
    reset_current_user_id,
    set_current_backpack_execution,
    set_current_drift_execution,
    set_current_event_emitter,
    set_current_market_context,
    set_current_user_id,
)
from agents.uploads import AgentAttachment
from agents.trading_style import (
    TRADING_STYLE_BALANCED,
    get_trading_style_guidance,
    normalize_trading_style,
)
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent:
    """Base agent class using Claude Agent SDK with memory and compression."""

    def __init__(
        self,
        name: str,
        system_prompt: str = "",
        scope_id: Optional[str] = None,
        user_id: Optional[str] = None,
        max_tokens: int = 4000,
        model: str = "claude-3-5-sonnet-20241022",
    ):
        """
        Initialize base agent.

        Args:
            name: Agent name
            system_prompt: System prompt for the agent
            scope_id: Optional scope ID for memory isolation
            user_id: Optional user ID for Mem0-backed long-term memory
            max_tokens: Max tokens before auto-compression
            model: Claude model to use (ignored if USE_OPENROUTER=true)
        """
        self.name = name
        self.system_prompt = system_prompt
        self.scope_id = scope_id
        self.user_id = user_id

        if settings.USE_OPENROUTER:
            self.model = settings.OPENROUTER_MODEL
            self.client = Anthropic(
                api_key=settings.OPENROUTER_API_KEY,
                base_url=settings.OPENROUTER_BASE_URL,
            )
            self.async_client = AsyncAnthropic(
                api_key=settings.OPENROUTER_API_KEY,
                base_url=settings.OPENROUTER_BASE_URL,
            )
            logger.info(f"Initialized agent with OpenRouter: {name} (model: {self.model})")
        else:
            self.model = model
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.async_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            logger.info(f"Initialized agent with Anthropic: {name} (model: {self.model})")

        self.memory = ConversationMemory()
        self.session_costs = get_openrouter_session_cost_service()
        self.compressor = ConversationCompressor(
            max_tokens=max_tokens,
            model=self.model,
            usage_callback=self._record_openrouter_usage,
        )
        self.mem0 = get_mem0_client()
        self.last_intent = AgentIntentContext.fallback("No request processed yet.")
        self.last_conversation_style = CONVERSATION_STYLE_NORMAL
        self.last_trading_style = TRADING_STYLE_BALANCED
        self.last_market_context = normalize_market_context(None)
        self.last_backpack_execution = normalize_backpack_execution(None)
        self.last_drift_execution = normalize_drift_execution(None)
        self.last_session_cost_summary: Optional[Dict[str, Any]] = None

        logger.info(f"Agent scope: {scope_id or 'global'}")

    def add_message(self, role: str, content: str) -> None:
        """
        Add message to conversation history with memory.

        Args:
            role: Message role (user/assistant)
            content: Message content
        """
        message = Message(role=role, content=content, timestamp=datetime.now())
        self.memory.add_message(message, self.scope_id)

    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history.

        Args:
            limit: Optional limit for messages

        Returns:
            List of messages as Claude-compatible dicts
        """
        messages = self.memory.get_messages(self.scope_id, limit)
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def clear_history(self) -> None:
        """Clear conversation history."""
        if self.scope_id:
            self.memory.clear_scope(self.scope_id)
        else:
            self.memory.clear_global()
        logger.info(f"Cleared history for agent: {self.name}")

    async def process(
        self,
        user_input: str,
        use_tools: bool = False,
        attachments: Optional[List[AgentAttachment]] = None,
        conversation_style: str = CONVERSATION_STYLE_NORMAL,
        trading_style: str = TRADING_STYLE_BALANCED,
        market_context: Optional[Dict[str, Any]] = None,
        backpack_execution: Optional[Dict[str, Any]] = None,
        drift_execution: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Process user input with auto-compression and optional multimodal attachments.

        Args:
            user_input: User input message
            use_tools: Whether to enable tool calling
            attachments: Optional uploaded files to send to the model
            conversation_style: Requested response style from the frontend
            trading_style: Requested trading-analysis style from the frontend
            market_context: Frontend market scope and market-state context

        Returns:
            Agent response
        """
        attachments = attachments or []
        conversation_style = normalize_conversation_style(conversation_style)
        trading_style = normalize_trading_style(trading_style)
        market_context = normalize_market_context(market_context)
        backpack_execution = normalize_backpack_execution(backpack_execution)
        drift_execution = normalize_drift_execution(drift_execution)
        self.last_conversation_style = conversation_style
        self.last_trading_style = trading_style
        self.last_market_context = market_context
        self.last_backpack_execution = backpack_execution
        self.last_drift_execution = drift_execution
        user_summary = self._build_memory_user_text(user_input, attachments)
        history = self.get_conversation_history()
        if self.compressor.needs_compression(history):
            logger.info(f"Auto-compressing conversation for agent: {self.name}")
            history = await self.compressor.compress(history)
        intent_context = await self._route_intent(user_input, history, market_context)
        self.last_intent = intent_context
        effective_system_prompt = await self._build_effective_system_prompt(
            user_input,
            intent_context,
            conversation_style,
            trading_style,
            market_context,
            backpack_execution,
            drift_execution,
        )

        messages = list(history)
        messages.append({
            "role": "user",
            "content": self._build_user_content(user_input, attachments),
        })

        try:
            if use_tools:
                response_text = await self._process_with_tools(
                    messages,
                    effective_system_prompt,
                    intent_context,
                )
            else:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=effective_system_prompt,
                    messages=messages,
                )
                self._record_openrouter_usage(response, "response")
                response_text = self._extract_response_text(response)

            self.last_session_cost_summary = self._get_session_cost_summary()
            self.add_message("user", user_summary)
            self.add_message("assistant", response_text)
            return response_text

        except Exception as exc:
            logger.error(f"Error processing message: {str(exc)}")
            error_msg = f"Error: {str(exc)}"
            self.add_message("user", user_summary)
            self.add_message("assistant", error_msg)
            return error_msg

    async def process_stream(
        self,
        user_input: str,
        event_emitter,
        use_tools: bool = False,
        attachments: Optional[List[AgentAttachment]] = None,
        conversation_style: str = CONVERSATION_STYLE_NORMAL,
        trading_style: str = TRADING_STYLE_BALANCED,
        market_context: Optional[Dict[str, Any]] = None,
        backpack_execution: Optional[Dict[str, Any]] = None,
        drift_execution: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Process user input and emit streaming UI/text events.

        Args:
            user_input: User input message
            event_emitter: Async callback receiving (event_name, payload)
            use_tools: Whether to enable tool calling
            attachments: Optional uploaded files
            conversation_style: Requested response style from the frontend
            trading_style: Requested trading-analysis style from the frontend
            market_context: Frontend market scope and market-state context

        Returns:
            Final agent response text
        """
        attachments = attachments or []
        conversation_style = normalize_conversation_style(conversation_style)
        trading_style = normalize_trading_style(trading_style)
        market_context = normalize_market_context(market_context)
        backpack_execution = normalize_backpack_execution(backpack_execution)
        drift_execution = normalize_drift_execution(drift_execution)
        self.last_conversation_style = conversation_style
        self.last_trading_style = trading_style
        self.last_market_context = market_context
        self.last_backpack_execution = backpack_execution
        self.last_drift_execution = drift_execution
        user_summary = self._build_memory_user_text(user_input, attachments)
        history = self.get_conversation_history()
        if self.compressor.needs_compression(history):
            logger.info(f"Auto-compressing conversation for agent: {self.name}")
            history = await self.compressor.compress(history)
        intent_context = await self._route_intent(user_input, history, market_context)
        self.last_intent = intent_context
        effective_system_prompt = await self._build_effective_system_prompt(
            user_input,
            intent_context,
            conversation_style,
            trading_style,
            market_context,
            backpack_execution,
            drift_execution,
        )

        messages = list(history)
        messages.append({
            "role": "user",
            "content": self._build_user_content(user_input, attachments),
        })

        try:
            if use_tools:
                response_text = await self._process_with_tools_stream(
                    messages,
                    effective_system_prompt,
                    event_emitter,
                    intent_context,
                )
            else:
                response_text = await self._stream_model_turn(
                    messages,
                    effective_system_prompt,
                    None,
                    event_emitter,
                )

            self.last_session_cost_summary = self._get_session_cost_summary()
            self.add_message("user", user_summary)
            self.add_message("assistant", response_text)
            return response_text
        except Exception as exc:
            logger.error(f"Error processing streaming message: {str(exc)}")
            error_msg = f"Error: {str(exc)}"
            self.add_message("user", user_summary)
            self.add_message("assistant", error_msg)
            raise

    async def _process_with_tools(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        intent_context: AgentIntentContext,
    ) -> str:
        """
        Process with tool calling support.

        Args:
            messages: Conversation messages
            system_prompt: Effective system prompt for this request

        Returns:
            Final response text
        """
        tools_schema = tool_registry.get_tools_schema(
            allowed_names=intent_context.allowed_tool_names
        )
        user_token = set_current_user_id(self.user_id)
        backpack_execution_token = set_current_backpack_execution(self.last_backpack_execution)
        drift_execution_token = set_current_drift_execution(self.last_drift_execution)
        market_context_token = set_current_market_context(self.last_market_context)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
                tools=tools_schema,
            )
            self._record_openrouter_usage(response, "response")

            if response.stop_reason == "tool_use":
                tool_results = []

                for content_block in response.content:
                    if content_block.type != "tool_use":
                        continue

                    tool_name = content_block.name
                    tool_input = content_block.input

                    logger.info(f"Executing tool: {tool_name}")
                    result = await tool_registry.execute(tool_name, tool_input)

                    if not result.success:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": self._format_tool_error(result),
                        })
                    else:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": str(result.data),
                        })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

                final_response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=system_prompt,
                    messages=messages,
                    tools=tools_schema,
                )
                self._record_openrouter_usage(final_response, "tool_followup")
                return self._extract_response_text(final_response)

            return self._extract_response_text(response)
        finally:
            reset_current_market_context(market_context_token)
            reset_current_drift_execution(drift_execution_token)
            reset_current_backpack_execution(backpack_execution_token)
            reset_current_user_id(user_token)

    async def _process_with_tools_stream(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        event_emitter,
        intent_context: AgentIntentContext,
    ) -> str:
        """
        Process with tool calling and SSE-friendly event emission.

        Args:
            messages: Conversation messages
            system_prompt: Effective system prompt
            event_emitter: Async event callback

        Returns:
            Final response text
        """
        tools_schema = tool_registry.get_tools_schema(
            allowed_names=intent_context.allowed_tool_names
        )
        user_token = set_current_user_id(self.user_id)
        backpack_execution_token = set_current_backpack_execution(self.last_backpack_execution)
        drift_execution_token = set_current_drift_execution(self.last_drift_execution)
        market_context_token = set_current_market_context(self.last_market_context)
        emitter_token = set_current_event_emitter(event_emitter)

        try:
            while True:
                final_message, response_text = await self._stream_model_round(
                    messages=messages,
                    system_prompt=system_prompt,
                    tools_schema=tools_schema,
                    event_emitter=event_emitter,
                )

                if final_message.stop_reason != "tool_use":
                    return response_text

                tool_results = []
                messages.append({"role": "assistant", "content": final_message.content})

                for content_block in final_message.content:
                    if content_block.type != "tool_use":
                        continue

                    tool_name = content_block.name
                    tool_input = content_block.input

                    logger.info(f"Executing tool: {tool_name}")
                    result = await tool_registry.execute(tool_name, tool_input)

                    if not result.success:
                        await event_emitter(
                            "error",
                            {
                                "type": "error",
                                "source": "tool",
                                "tool_name": tool_name,
                                "message": result.error,
                                "details": result.error_details or {},
                            },
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": self._format_tool_error(result),
                        })
                    else:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": str(result.data),
                        })

                messages.append({"role": "user", "content": tool_results})
        finally:
            reset_current_event_emitter(emitter_token)
            reset_current_market_context(market_context_token)
            reset_current_drift_execution(drift_execution_token)
            reset_current_backpack_execution(backpack_execution_token)
            reset_current_user_id(user_token)

    async def _stream_model_round(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools_schema,
        event_emitter,
    ):
        """Stream one model round and return the final message plus accumulated text."""
        text_parts: List[str] = []

        async with self.async_client.messages.stream(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
            tools=tools_schema,
        ) as stream:
            async for text in stream.text_stream:
                if text:
                    text_parts.append(text)
                    await event_emitter(
                        "assistant_delta",
                        {
                            "type": "assistant_delta",
                            "delta": text,
                        },
                    )

            final_message = await stream.get_final_message()
            self._record_openrouter_usage(final_message, "stream_round")

        return final_message, "".join(text_parts).strip()

    async def _stream_model_turn(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools_schema,
        event_emitter,
    ) -> str:
        """Stream a single assistant response without a tool loop."""
        _, response_text = await self._stream_model_round(
            messages=messages,
            system_prompt=system_prompt,
            tools_schema=tools_schema,
            event_emitter=event_emitter,
        )
        return response_text

    def _build_user_content(
        self,
        user_input: str,
        attachments: List[AgentAttachment],
    ) -> str | List[Dict[str, Any]]:
        """Build a Claude-compatible user content block list when attachments are present."""
        if not attachments:
            return user_input

        content: List[Dict[str, Any]] = [{"type": "text", "text": user_input}]
        for attachment in attachments:
            content.append(self._attachment_to_content_block(attachment))
        return content

    def _attachment_to_content_block(self, attachment: AgentAttachment) -> Dict[str, Any]:
        """Convert a local attachment into an Anthropic/OpenRouter content block."""
        encoded_data = base64.b64encode(
            self._read_attachment_bytes(attachment)
        ).decode("ascii")

        if attachment.kind == "image":
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": attachment.content_type,
                    "data": encoded_data,
                },
            }

        return {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": attachment.content_type,
                "data": encoded_data,
            },
        }

    def _read_attachment_bytes(self, attachment: AgentAttachment) -> bytes:
        """Read a local attachment from disk."""
        with open(attachment.path, "rb") as file_handle:
            return file_handle.read()

    def _build_memory_user_text(
        self,
        user_input: str,
        attachments: List[AgentAttachment],
    ) -> str:
        """Persist only a text summary of multimodal inputs into conversation memory."""
        if not attachments:
            return user_input

        attachment_summaries = ", ".join(
            f"{attachment.filename} ({attachment.content_type})"
            for attachment in attachments
        )
        return f"{user_input}\n\n[Attachments: {attachment_summaries}]"

    async def _build_effective_system_prompt(
        self,
        user_input: str,
        intent_context: Optional[AgentIntentContext] = None,
        conversation_style: str = CONVERSATION_STYLE_NORMAL,
        trading_style: str = TRADING_STYLE_BALANCED,
        market_context: Optional[Dict[str, Any]] = None,
        backpack_execution: Optional[Dict[str, Any]] = None,
        drift_execution: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Append long-term memory and intent guidance to the system prompt."""
        intent_context = intent_context or AgentIntentContext.fallback()
        normalized_style = normalize_conversation_style(conversation_style)
        normalized_trading_style = normalize_trading_style(trading_style)
        normalized_market_context = normalize_market_context(market_context)
        normalized_backpack_execution = normalize_backpack_execution(backpack_execution)
        normalized_drift_execution = normalize_drift_execution(drift_execution)
        base_prompt = (
            f"{self.system_prompt}\n\n"
            "Current routing context:\n"
            f"- intent: {intent_context.intent}\n"
            f"- user_goal_type: {intent_context.user_goal_type}\n"
            f"- confidence: {intent_context.confidence}\n"
            f"- goal_summary: {intent_context.goal_summary or 'n/a'}\n"
            f"- analysis_mode: {intent_context.analysis_mode}\n"
            f"- analysis_scope: {intent_context.analysis_scope}\n"
            f"- indicator_preference: {intent_context.indicator_preference}\n"
            f"- need_indicator_confirmation: "
            f"{str(intent_context.need_indicator_confirmation).lower()}\n"
            f"- inferred_indicator_hint: {intent_context.inferred_indicator_hint or 'n/a'}\n"
            f"- response_language: {intent_context.response_language}\n"
            f"- should_clarify: {str(intent_context.should_clarify).lower()}\n"
            f"- clarification_reason: {intent_context.clarification_reason or 'n/a'}\n"
            f"- suggested_hint_title: {intent_context.suggested_hint_title or 'n/a'}\n"
            f"- suggested_hint_options: "
            f"{json.dumps(intent_context.suggested_hint_options, ensure_ascii=False)}\n"
            f"- conversation_style: {normalized_style}\n"
            f"- trading_style: {normalized_trading_style}\n"
            f"- market_context: {json.dumps(normalized_market_context, ensure_ascii=False)}\n"
            f"- backpack_execution: {json.dumps(normalized_backpack_execution, ensure_ascii=False)}\n"
            f"- drift_execution: {json.dumps(normalized_drift_execution, ensure_ascii=False)}\n"
            f"- intent_guidance: {intent_context.system_guidance}\n"
            f"- goal_guidance: {intent_context.goal_guidance}\n"
            f"- analysis_guidance: {intent_context.analysis_guidance}\n"
            f"- language_guidance: {intent_context.language_guidance}\n"
            f"- style_guidance: {get_conversation_style_guidance(normalized_style)}\n"
            f"- trading_style_guidance: {get_trading_style_guidance(normalized_trading_style)}\n"
            f"- market_context_guidance: {get_market_context_guidance(normalized_market_context)}\n"
            f"- backpack_execution_guidance: {get_backpack_execution_guidance(normalized_backpack_execution)}\n"
            f"- drift_execution_guidance: {get_drift_execution_guidance(normalized_drift_execution)}\n"
            f"- clarification_guidance: {intent_context.clarification_guidance}"
        )

        if not self.user_id:
            return base_prompt

        try:
            memory_context = await self.mem0.get_context(self.user_id, user_input)
        except Mem0Error as exc:
            logger.warning(f"Mem0 context unavailable for user '{self.user_id}': {exc}")
            return base_prompt

        if not memory_context:
            return base_prompt

        return (
            f"{base_prompt}\n\n"
            f"{memory_context}\n\n"
            "Use long-term memory only when it is relevant to the user's request."
        )

    async def _route_intent(
        self,
        user_input: str,
        history: List[Dict[str, Any]],
        market_context: Optional[Dict[str, Any]] = None,
    ) -> AgentIntentContext:
        """Route the latest user message into an intent context using the model."""
        prompt = build_intent_prompt(user_input, history, market_context)
        try:
            response = await self.async_client.messages.create(
                model=self.model,
                max_tokens=256,
                system=(
                    "You are an intent router for a trading assistant. "
                    "Return only valid JSON."
                ),
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            self._record_openrouter_usage(response, "intent_router")
        except Exception as exc:
            logger.warning(f"Intent routing failed, using fallback: {exc}")
            return AgentIntentContext.fallback(f"Router request failed: {exc}")

        parsed = parse_intent_response(self._extract_response_text(response))
        logger.info(
            "Intent routed: intent=%s confidence=%s groups=%s",
            parsed.intent,
            parsed.confidence,
            ",".join(parsed.preferred_tool_groups),
        )
        return parsed

    def _extract_response_text(self, response: Any) -> str:
        """Extract text from a Claude/OpenRouter response."""
        parts: List[str] = []
        for block in getattr(response, "content", []):
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "\n".join(parts).strip()

    def _record_openrouter_usage(self, response: Any, phase: str) -> Optional[Dict[str, Any]]:
        """Record one OpenRouter usage event for the current scope when available."""
        if not settings.USE_OPENROUTER or not self.scope_id:
            return None

        usage = self._extract_usage_payload(response)
        if not usage:
            return None

        try:
            summary = self.session_costs.record_usage(
                scope_id=self.scope_id,
                user_id=self.user_id,
                model_id=self.model,
                usage=usage,
                phase=phase,
            )
            self.last_session_cost_summary = summary
            return summary
        except Exception as exc:
            logger.warning(f"Failed to record OpenRouter session cost usage: {exc}")
            return None

    def _get_session_cost_summary(self) -> Optional[Dict[str, Any]]:
        """Return the latest accumulated session cost summary for this scope."""
        if not self.scope_id:
            return None
        try:
            return self.session_costs.get_scope_summary(scope_id=self.scope_id)
        except Exception as exc:
            logger.warning(f"Failed to load OpenRouter session cost summary: {exc}")
            return None

    def _extract_usage_payload(self, response: Any) -> Optional[Dict[str, Any]]:
        """Extract usage metrics from Anthropic/OpenRouter response objects."""
        usage = getattr(response, "usage", None)
        if usage is None:
            return None

        if isinstance(usage, dict):
            payload = dict(usage)
        elif hasattr(usage, "model_dump"):
            payload = usage.model_dump()
        else:
            payload = {}
            for field in (
                "input_tokens",
                "output_tokens",
                "cache_creation_input_tokens",
                "cache_read_input_tokens",
            ):
                value = getattr(usage, field, None)
                if value is not None:
                    payload[field] = value

        if not payload:
            return None

        if not any(int(payload.get(key) or 0) for key in ("input_tokens", "output_tokens")):
            return None
        return payload

    def _format_tool_error(self, result: ToolResult) -> str:
        """
        Format tool error with detailed explanation.

        Args:
            result: Tool result with error

        Returns:
            Formatted error message
        """
        error_msg = f"Tool execution failed: {result.error}\n\n"

        if result.error_details:
            error_msg += "Details:\n"

            if "validation_errors" in result.error_details:
                error_msg += "\nParameter Validation Errors:\n"
                for err in result.error_details["validation_errors"]:
                    error_msg += f"  - {err['parameter']}: {err['error']}\n"
                    if "description" in err:
                        error_msg += f"    Expected: {err['description']}\n"

            if "expected_parameters" in result.error_details:
                error_msg += "\nExpected Parameters:\n"
                for param in result.error_details["expected_parameters"]:
                    required = "required" if param["required"] else "optional"
                    error_msg += (
                        f"  - {param['name']} ({param['type']}, {required}): "
                        f"{param['description']}\n"
                    )

            if "provided_parameters" in result.error_details:
                provided = ", ".join(result.error_details["provided_parameters"])
                error_msg += f"\nYou provided: {provided}\n"

            if "suggestion" in result.error_details:
                error_msg += f"\nSuggestion: {result.error_details['suggestion']}\n"

        return error_msg
