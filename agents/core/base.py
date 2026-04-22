"""Base agent class for Claude Agent SDK."""
import base64
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from anthropic import Anthropic, AsyncAnthropic

from agents.compression import ConversationCompressor
from agents.pipeline.conversation_style import (
    CONVERSATION_STYLE_NORMAL,
    get_conversation_style_guidance,
    normalize_conversation_style,
)
from agents.pipeline.execution_gate import (
    get_execution_gate_guidance,
    merge_legacy_execution_gates,
    normalize_execution_gate,
)
from agents.openrouter import get_openrouter_session_cost_service
from agents.service_costs import get_monitoring_cost_service
from agents.pipeline.intent_router import AgentIntentContext, build_intent_prompt, parse_intent_response
from agents.pipeline.artifacts import get_pipeline_artifact_service
from agents.memory import ConversationMemory, Mem0Error, Message, get_mem0_client
from agents.pipeline.market_context import get_market_context_guidance, normalize_market_context
from agents.pipeline.tool_preferences import (
    get_blocked_tool_names,
    get_tool_preferences_guidance,
    normalize_tool_preferences,
)
from agents.core.graph_executor import (
    AgentNodeExecutionContext,
    build_default_graph_executor,
)
from agents.pipeline.pipeline import AgentPipelineTrace, build_pipeline_trace
from agents.tools import ToolResult, tool_registry
from agents.tools.core.runtime_context import (
    reset_current_event_emitter,
    reset_current_execution_gate,
    reset_current_market_context,
    reset_current_scope_id,
    reset_current_user_id,
    set_current_event_emitter,
    set_current_execution_gate,
    set_current_market_context,
    set_current_scope_id,
    set_current_user_id,
)
from agents.uploads import AgentAttachment
from agents.pipeline.trading_style import (
    TRADING_STYLE_BALANCED,
    get_trading_style_guidance,
    normalize_trading_style,
)
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class AgentExecutionError(RuntimeError):
    """Raised when agent execution fails after converting to a safe user-facing message."""


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
        self.monitoring_costs = get_monitoring_cost_service()
        self.pipeline_artifacts = get_pipeline_artifact_service()
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
        self.last_execution_gate = normalize_execution_gate(None)
        self.last_tool_preferences = normalize_tool_preferences(None)
        self.last_pipeline_artifacts: List[Dict[str, Any]] = []
        self.last_session_cost_summary: Optional[Dict[str, Any]] = None
        self.last_service_cost_summary: Optional[Dict[str, Any]] = None
        self.last_pipeline_trace: Optional[AgentPipelineTrace] = None
        self.last_safe_error_message: Optional[str] = None
        self.graph_executor = build_default_graph_executor()

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

    async def _prepare_turn(
        self,
        *,
        user_input: str,
        attachments: List[AgentAttachment],
        conversation_style: str,
        trading_style: str,
        market_context: Optional[Dict[str, Any]],
        execution_gate: Optional[Dict[str, Any]],
        tool_preferences: Optional[Dict[str, Any]],
    ) -> Tuple[str, List[Dict[str, Any]], AgentIntentContext, str]:
        """Normalize inputs, route intent, and build a pipeline-ready prompt."""
        conversation_style = normalize_conversation_style(conversation_style)
        trading_style = normalize_trading_style(trading_style)
        market_context = normalize_market_context(market_context)
        execution_gate = merge_legacy_execution_gates(execution_gate=execution_gate)
        tool_preferences = normalize_tool_preferences(tool_preferences)
        self.last_conversation_style = conversation_style
        self.last_trading_style = trading_style
        self.last_market_context = market_context
        self.last_execution_gate = execution_gate
        self.last_tool_preferences = tool_preferences
        self.last_pipeline_artifacts = []
        self.last_safe_error_message = None

        user_summary = self._build_memory_user_text(user_input, attachments)
        history = self.get_conversation_history()
        if self.compressor.needs_compression(history):
            logger.info(f"Auto-compressing conversation for agent: {self.name}")
            history = await self.compressor.compress(history)

        intent_context = await self._route_intent(user_input, history, market_context)
        self.last_intent = intent_context
        self.last_pipeline_trace = build_pipeline_trace(
            entry_agent=self.name,
            intent_context=intent_context,
            user_input=user_input,
            market_context=market_context,
            execution_gate=execution_gate,
        )

        effective_system_prompt = await self._build_effective_system_prompt(
            user_input,
            intent_context,
            conversation_style,
            trading_style,
            market_context,
            execution_gate,
            tool_preferences,
        )

        messages = list(history)
        messages.append({
            "role": "user",
            "content": self._build_user_content(user_input, attachments),
        })
        return user_summary, messages, intent_context, effective_system_prompt

    async def _execute_tool_for_node(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Execute one tool on behalf of a pipeline node with shared failure tracking."""
        if tool_name in get_blocked_tool_names(self.last_tool_preferences):
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' is disabled by the current assist settings.",
            )
        result = await tool_registry.execute(tool_name, arguments)
        if not result.success and self.last_pipeline_trace is not None:
            self.last_pipeline_trace.record_tool_failure(
                tool_name,
                result.error or "Unknown tool failure",
            )
        return result

    def _persist_pipeline_artifact(
        self,
        *,
        node_name: str,
        kind: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Persist one session-scoped pipeline artifact when scope storage is available."""
        if not self.scope_id:
            return None

        artifact = self.pipeline_artifacts.record_artifact(
            scope_id=self.scope_id,
            user_id=self.user_id,
            node_name=node_name,
            kind=kind,
            payload=payload,
            metadata=metadata,
        )
        self.last_pipeline_artifacts.append(artifact)
        if self.last_pipeline_trace is not None:
            self.last_pipeline_trace.add_artifact(artifact)
        return artifact

    async def _run_pipeline_nodes(
        self,
        *,
        user_input: str,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        intent_context: AgentIntentContext,
        event_emitter=None,
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Run composable pre-response pipeline nodes before the main runtime answer."""
        pipeline = self.last_pipeline_trace
        if pipeline is None or not pipeline.pipeline_nodes:
            return messages, system_prompt

        self._update_pipeline_stage(
            "graph_execution",
            status="running",
            summary="Executing planned pre-response pipeline nodes.",
            metadata={"pipeline_nodes": [node.name for node in pipeline.pipeline_nodes]},
        )

        user_token = set_current_user_id(self.user_id)
        scope_token = set_current_scope_id(self.scope_id)
        execution_gate_token = set_current_execution_gate(self.last_execution_gate)
        market_context_token = set_current_market_context(self.last_market_context)
        emitter_token = set_current_event_emitter(event_emitter) if event_emitter else None

        try:
            context = AgentNodeExecutionContext(
                agent=self,
                user_input=user_input,
                messages=list(messages),
                system_prompt=system_prompt,
                intent_context=intent_context,
                market_context=self.last_market_context,
                scope_id=self.scope_id,
                user_id=self.user_id,
                event_emitter=event_emitter,
                call_tool=self._execute_tool_for_node,
                persist_artifact=self._persist_pipeline_artifact,
            )
            context = await self.graph_executor.execute(
                plans=pipeline.pipeline_nodes,
                context=context,
            )
        finally:
            if emitter_token is not None:
                reset_current_event_emitter(emitter_token)
            reset_current_market_context(market_context_token)
            reset_current_execution_gate(execution_gate_token)
            reset_current_scope_id(scope_token)
            reset_current_user_id(user_token)

        degraded_nodes = [node.name for node in pipeline.pipeline_nodes if node.status in {"degraded", "failed"}]
        self._update_pipeline_stage(
            "graph_execution",
            status="completed" if not degraded_nodes else "degraded",
            summary=(
                "Completed planned pre-response pipeline nodes."
                if not degraded_nodes
                else "Completed planned pipeline nodes with degraded specialist context."
            ),
            metadata={
                "executed_nodes": [node.name for node in pipeline.pipeline_nodes],
                "degraded_nodes": degraded_nodes,
                "node_observations": context.observations,
                "artifact_count": len(self.last_pipeline_artifacts),
            },
        )
        pipeline.next_agent_status = pipeline.resolve_next_agent_status()
        if degraded_nodes and self.last_pipeline_trace is not None:
            self.last_pipeline_trace.mark_fallback(
                "pipeline_node_degraded",
                f"Pipeline nodes degraded: {', '.join(degraded_nodes)}",
            )

        return context.messages, context.system_prompt

    def _update_pipeline_stage(
        self,
        name: str,
        *,
        status: str,
        summary: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update the stored pipeline trace when present."""
        if self.last_pipeline_trace is None:
            return
        self.last_pipeline_trace.update_stage(
            name,
            status=status,
            summary=summary,
            metadata=metadata,
        )

    def _get_effective_allowed_tool_names(
        self,
        intent_context: AgentIntentContext,
    ) -> Optional[set[str]]:
        """Resolve the tool surface after applying pipeline-node restrictions."""
        allowed_names = intent_context.allowed_tool_names
        pipeline = self.last_pipeline_trace
        if allowed_names is None:
            effective_names: Optional[set[str]] = None
        else:
            effective_names = set(allowed_names)

        if pipeline is None:
            return effective_names

        blocked_names: set[str] = set()
        allow_lists: list[set[str]] = []
        for node in pipeline.pipeline_nodes:
            blocked_names.update(node.config.get("llm_blocked_tool_names", []))
            explicit_allowed_names = node.config.get("llm_allowed_tool_names", [])
            if explicit_allowed_names:
                allow_lists.append(set(explicit_allowed_names))

        if allow_lists:
            allowed_by_nodes = set().union(*allow_lists)
            if effective_names is None:
                effective_names = allowed_by_nodes
            else:
                effective_names.intersection_update(allowed_by_nodes)

        if effective_names is None:
            return None

        if blocked_names:
            effective_names.difference_update(blocked_names)

        blocked_by_preferences = get_blocked_tool_names(self.last_tool_preferences)
        if effective_names is None:
            if not blocked_by_preferences:
                return None
            return {
                tool.name
                for tool in tool_registry.list_tools()
                if tool.name not in blocked_by_preferences
            }

        effective_names.difference_update(blocked_by_preferences)
        return effective_names

    def _finalize_pipeline(self, status: str) -> None:
        """Set final pipeline status when a trace exists."""
        if self.last_pipeline_trace is None:
            return
        self.last_pipeline_trace.finalize(status)

    def _build_user_safe_error_response(
        self,
        exc: Exception,
        intent_context: Optional[AgentIntentContext] = None,
    ) -> str:
        """Build a user-safe fallback message instead of leaking raw backend errors."""
        intent_context = intent_context or AgentIntentContext.fallback()
        fallback_by_intent = {
            "broker_execution": (
                "I could not safely continue the execution workflow right now. "
                "I can still help you review execution readiness, open orders, or the trade setup before you retry."
            ),
            "portfolio_review": (
                "I hit a backend issue while reviewing the portfolio data. "
                "I can still help you think through the portfolio at a high level or you can retry once the data path is healthy."
            ),
            "position_management": (
                "I could not complete the position-management workflow right now. "
                "I can still help you think through stop logic, invalidation, or next-step scenarios."
            ),
            "memory_lookup": (
                "I could not access the memory layer right now. "
                "If you want, I can still answer from the current conversation context only."
            ),
        }
        message = fallback_by_intent.get(
            intent_context.intent,
            (
                "I hit a backend issue while working through that request. "
                "I can still help with a safer high-level answer, or you can retry once the failing path is available."
            ),
        )
        logger.warning(
            "Returning safe agent fallback message for intent=%s error_type=%s error=%s",
            intent_context.intent,
            type(exc).__name__,
            str(exc),
        )
        return message

    async def process(
        self,
        user_input: str,
        use_tools: bool = False,
        attachments: Optional[List[AgentAttachment]] = None,
        conversation_style: str = CONVERSATION_STYLE_NORMAL,
        trading_style: str = TRADING_STYLE_BALANCED,
        market_context: Optional[Dict[str, Any]] = None,
        execution_gate: Optional[Dict[str, Any]] = None,
        tool_preferences: Optional[Dict[str, Any]] = None,
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
        (
            user_summary,
            messages,
            intent_context,
            effective_system_prompt,
        ) = await self._prepare_turn(
            user_input=user_input,
            attachments=attachments or [],
            conversation_style=conversation_style,
            trading_style=trading_style,
            market_context=market_context,
            execution_gate=execution_gate,
            tool_preferences=tool_preferences,
        )

        try:
            messages, effective_system_prompt = await self._run_pipeline_nodes(
                user_input=user_input,
                messages=messages,
                system_prompt=effective_system_prompt,
                intent_context=intent_context,
            )
            self._update_pipeline_stage(
                "execution",
                status="running",
                summary="Executing the request inside the current runtime agent.",
            )
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
            self.last_service_cost_summary = self._get_service_cost_summary()
            self._update_pipeline_stage(
                "execution",
                status="completed",
                summary="Completed execution in the current runtime agent.",
                metadata={"used_tools": bool(use_tools)},
            )
            self._update_pipeline_stage(
                "completion",
                status="completed",
                summary="Final response assembled successfully.",
            )
            self._finalize_pipeline("completed")
            self.add_message("user", user_summary)
            self.add_message("assistant", response_text)
            return response_text

        except Exception as exc:
            logger.error(f"Error processing message: {str(exc)}")
            error_msg = self._build_user_safe_error_response(exc, intent_context)
            self.last_safe_error_message = error_msg
            self._update_pipeline_stage(
                "execution",
                status="failed",
                summary="Execution failed and switched to a safe fallback response.",
                metadata={"error_type": type(exc).__name__},
            )
            self._update_pipeline_stage(
                "completion",
                status="degraded",
                summary="Returned a safe fallback response instead of a raw error.",
            )
            self._finalize_pipeline("degraded")
            self.last_session_cost_summary = self._get_session_cost_summary()
            self.last_service_cost_summary = self._get_service_cost_summary()
            if self.last_pipeline_trace:
                self.last_pipeline_trace.mark_fallback(
                    "safe_error_response",
                    f"{type(exc).__name__}: {exc}",
                )
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
        execution_gate: Optional[Dict[str, Any]] = None,
        tool_preferences: Optional[Dict[str, Any]] = None,
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
        (
            user_summary,
            messages,
            intent_context,
            effective_system_prompt,
        ) = await self._prepare_turn(
            user_input=user_input,
            attachments=attachments or [],
            conversation_style=conversation_style,
            trading_style=trading_style,
            market_context=market_context,
            execution_gate=execution_gate,
            tool_preferences=tool_preferences,
        )

        try:
            messages, effective_system_prompt = await self._run_pipeline_nodes(
                user_input=user_input,
                messages=messages,
                system_prompt=effective_system_prompt,
                intent_context=intent_context,
                event_emitter=event_emitter,
            )
            self._update_pipeline_stage(
                "execution",
                status="running",
                summary="Streaming the request through the current runtime agent.",
            )
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
            self.last_service_cost_summary = self._get_service_cost_summary()
            self._update_pipeline_stage(
                "execution",
                status="completed",
                summary="Completed streaming execution in the current runtime agent.",
                metadata={"used_tools": bool(use_tools)},
            )
            self._update_pipeline_stage(
                "completion",
                status="completed",
                summary="Streaming finished successfully.",
            )
            self._finalize_pipeline("completed")
            self.add_message("user", user_summary)
            self.add_message("assistant", response_text)
            return response_text
        except Exception as exc:
            logger.error(f"Error processing streaming message: {str(exc)}")
            safe_error = self._build_user_safe_error_response(exc, intent_context)
            self.last_safe_error_message = safe_error
            self._update_pipeline_stage(
                "execution",
                status="failed",
                summary="Streaming execution failed and switched to a safe fallback message.",
                metadata={"error_type": type(exc).__name__},
            )
            self._update_pipeline_stage(
                "completion",
                status="failed",
                summary="Streaming ended with a fallback-safe error state.",
            )
            self._finalize_pipeline("failed")
            self.last_session_cost_summary = self._get_session_cost_summary()
            self.last_service_cost_summary = self._get_service_cost_summary()
            if self.last_pipeline_trace:
                self.last_pipeline_trace.mark_fallback(
                    "safe_stream_error",
                    f"{type(exc).__name__}: {exc}",
                )
            self.add_message("user", user_summary)
            self.add_message("assistant", safe_error)
            raise AgentExecutionError(safe_error) from exc

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
            allowed_names=self._get_effective_allowed_tool_names(intent_context)
        )
        user_token = set_current_user_id(self.user_id)
        scope_token = set_current_scope_id(self.scope_id)
        execution_gate_token = set_current_execution_gate(self.last_execution_gate)
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
                tool_failure_count = 0

                for content_block in response.content:
                    if content_block.type != "tool_use":
                        continue

                    tool_name = content_block.name
                    tool_input = content_block.input

                    logger.info(f"Executing tool: {tool_name}")
                    result = await tool_registry.execute(tool_name, tool_input)

                    if not result.success:
                        tool_failure_count += 1
                        if self.last_pipeline_trace is not None:
                            self.last_pipeline_trace.record_tool_failure(
                                tool_name,
                                result.error or "Unknown tool failure",
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
                            "content": self._build_tool_result_content(tool_name, result.data),
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
                self._update_pipeline_stage(
                    "execution",
                    status="completed" if tool_failure_count == 0 else "degraded",
                    summary=(
                        "Completed the tool loop and produced a follow-up response."
                        if tool_failure_count == 0
                        else "Completed the tool loop with some degraded tool results."
                    ),
                    metadata={"tool_failure_count": tool_failure_count},
                )
                return self._extract_response_text(final_response)

            self._update_pipeline_stage(
                "execution",
                status="completed",
                summary="Answered directly without needing tool calls.",
                metadata={"tool_failure_count": 0},
            )
            return self._extract_response_text(response)
        finally:
            reset_current_market_context(market_context_token)
            reset_current_execution_gate(execution_gate_token)
            reset_current_scope_id(scope_token)
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
            allowed_names=self._get_effective_allowed_tool_names(intent_context)
        )
        user_token = set_current_user_id(self.user_id)
        scope_token = set_current_scope_id(self.scope_id)
        execution_gate_token = set_current_execution_gate(self.last_execution_gate)
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
                tool_failure_count = 0
                messages.append({"role": "assistant", "content": final_message.content})

                for content_block in final_message.content:
                    if content_block.type != "tool_use":
                        continue

                    tool_name = content_block.name
                    tool_input = content_block.input

                    logger.info(f"Executing tool: {tool_name}")
                    result = await tool_registry.execute(tool_name, tool_input)

                    if not result.success:
                        tool_failure_count += 1
                        if self.last_pipeline_trace is not None:
                            self.last_pipeline_trace.record_tool_failure(
                                tool_name,
                                result.error or "Unknown tool failure",
                            )
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
                            "content": self._build_tool_result_content(tool_name, result.data),
                        })

                self._update_pipeline_stage(
                    "execution",
                    status="running" if tool_failure_count == 0 else "degraded",
                    summary=(
                        "Streaming tool loop is continuing."
                        if tool_failure_count == 0
                        else "Streaming tool loop continued with degraded tool results."
                    ),
                    metadata={"tool_failure_count": tool_failure_count},
                )
                messages.append({"role": "user", "content": tool_results})
        finally:
            reset_current_event_emitter(emitter_token)
            reset_current_market_context(market_context_token)
            reset_current_execution_gate(execution_gate_token)
            reset_current_scope_id(scope_token)
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

    def _build_tool_result_content(self, tool_name: str, data: Any) -> Any:
        """Format tool results for the model, including multimodal TradingView screenshots."""
        if tool_name == "tv_capture_screenshot" and isinstance(data, dict):
            summary_payload = {
                key: value
                for key, value in data.items()
                if key != "agent_image"
            }
            summary_text = (
                "TradingView screenshot captured successfully.\n"
                f"{json.dumps(summary_payload, ensure_ascii=False)}"
            )

            agent_image = data.get("agent_image")
            if isinstance(agent_image, dict):
                media_type = str(agent_image.get("content_type") or "").strip()
                encoded = str(agent_image.get("data_base64") or "").strip()
                if media_type and encoded:
                    return [
                        {"type": "text", "text": summary_text},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": encoded,
                            },
                        },
                    ]

            return summary_text

        if isinstance(data, (dict, list)):
            return json.dumps(data, ensure_ascii=False)
        return str(data)

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
        execution_gate: Optional[Dict[str, Any]] = None,
        tool_preferences: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Append long-term memory and intent guidance to the system prompt."""
        intent_context = intent_context or AgentIntentContext.fallback()
        normalized_style = normalize_conversation_style(conversation_style)
        normalized_trading_style = normalize_trading_style(trading_style)
        normalized_market_context = normalize_market_context(market_context)
        normalized_execution_gate = normalize_execution_gate(execution_gate)
        normalized_tool_preferences = normalize_tool_preferences(tool_preferences)
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
            f"- execution_gate: {json.dumps(normalized_execution_gate, ensure_ascii=False)}\n"
            f"- tool_preferences: {json.dumps(normalized_tool_preferences, ensure_ascii=False)}\n"
            f"- next_agent_target: "
            f"{getattr(self.last_pipeline_trace, 'selected_next_agent', 'general_specialist')}\n"
            f"- architecture_mode: "
            f"{getattr(self.last_pipeline_trace, 'architecture_mode', 'router_ready_single_runtime')}\n"
            f"- intent_guidance: {intent_context.system_guidance}\n"
            f"- goal_guidance: {intent_context.goal_guidance}\n"
            f"- analysis_guidance: {intent_context.analysis_guidance}\n"
            f"- language_guidance: {intent_context.language_guidance}\n"
            f"- style_guidance: {get_conversation_style_guidance(normalized_style)}\n"
            f"- trading_style_guidance: {get_trading_style_guidance(normalized_trading_style)}\n"
            f"- market_context_guidance: {get_market_context_guidance(normalized_market_context)}\n"
            f"- execution_gate_guidance: {get_execution_gate_guidance(normalized_execution_gate)}\n"
            f"- tool_preferences_guidance: {get_tool_preferences_guidance(normalized_tool_preferences)}\n"
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
            self.last_service_cost_summary = self._get_service_cost_summary()
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

    def _get_service_cost_summary(self) -> Optional[Dict[str, Any]]:
        """Return the latest combined model and monitoring cost summary for this scope."""
        if not self.scope_id:
            return None

        model_summary = self._get_session_cost_summary()
        try:
            monitor_summary = self.monitoring_costs.get_scope_summary(scope_id=self.scope_id)
        except Exception as exc:
            logger.warning(f"Failed to load monitoring cost summary: {exc}")
            monitor_summary = None

        if not model_summary and not monitor_summary:
            return None

        currency = "USD"
        created_at = None
        updated_at = None
        if model_summary:
            currency = model_summary.get("currency", currency)
            created_at = model_summary.get("created_at")
            updated_at = model_summary.get("updated_at")
        if monitor_summary:
            currency = monitor_summary.get("currency", currency)
            created_at = min(
                [value for value in [created_at, monitor_summary.get("created_at")] if value],
                default=created_at or monitor_summary.get("created_at"),
            )
            updated_at = max(
                [value for value in [updated_at, monitor_summary.get("updated_at")] if value],
                default=updated_at or monitor_summary.get("updated_at"),
            )

        return {
            "scope_id": self.scope_id,
            "user_id": self.user_id or (model_summary or {}).get("user_id") or (monitor_summary or {}).get("user_id"),
            "currency": currency,
            "model_cost_usd": round(float((model_summary or {}).get("estimated_cost_usd") or 0.0), 10),
            "monitor_cost_usd": round(float((monitor_summary or {}).get("total_cost_usd") or 0.0), 10),
            "total_cost_usd": round(
                float((model_summary or {}).get("estimated_cost_usd") or 0.0)
                + float((monitor_summary or {}).get("total_cost_usd") or 0.0),
                10,
            ),
            "session_cost": model_summary,
            "monitoring_cost": monitor_summary,
            "created_at": created_at,
            "updated_at": updated_at,
        }

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
