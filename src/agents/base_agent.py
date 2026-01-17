"""Base agent class using MCP tools."""

from typing import Any, Dict, List, Optional
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_anthropic import ChatAnthropic
from langchain.tools import Tool
import structlog
import asyncio

from ..mcp_server.server import OntologyMCPServer

logger = structlog.get_logger()


class BaseAgent:
    """
    Base agent class that uses MCP tools for semantic queries.
    
    Agents use the ontology MCP server to query databases using
    semantic queries instead of raw SQL.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        mcp_server: OntologyMCPServer,
        claude_api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.3
    ):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            description: Agent description
            mcp_server: MCP server instance
            claude_api_key: Anthropic API key (optional)
            model: Claude model to use
            temperature: LLM temperature
        """
        self.name = name
        self.description = description
        self.mcp_server = mcp_server
        
        # Initialize LLM
        if claude_api_key:
            self.llm = ChatAnthropic(
                anthropic_api_key=claude_api_key,
                model_name=model,
                temperature=temperature
            )
        else:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            
            self.llm = ChatAnthropic(
                anthropic_api_key=api_key,
                model_name=model,
                temperature=temperature
            )
        
        # Create tools from MCP server
        self.tools = self._create_tools()
        
        # Create agent
        self.agent_executor = self._create_agent_executor()
        
        logger.info("Agent initialized", name=name)
    
    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools from MCP server tools."""
        tools = []
        
        mcp_tools = self.mcp_server.get_tools()
        
        for mcp_tool in mcp_tools:
            tool = Tool(
                name=mcp_tool["name"],
                description=mcp_tool.get("description", ""),
                func=self._tool_func_factory(mcp_tool["name"])
            )
            tools.append(tool)
        
        logger.info("Agent tools created", tool_count=len(tools))
        return tools
    
    def _tool_func_factory(self, tool_name: str):
        """Create a tool function for a given MCP tool."""
        def tool_func(query: str) -> str:
            """Execute MCP tool with query."""
            try:
                # Parse query for limit/offset if needed
                args = {"query": query, "limit": 10, "offset": 0}
                
                # Execute tool (run async function synchronously)
                try:
                    # Try to get existing event loop
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is running, we need to create a task
                        import concurrent.futures
                        import threading
                        result_container = {}
                        
                        def run_in_thread():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                result_container['result'] = new_loop.run_until_complete(
                                    self.mcp_server.execute_tool(tool_name, args)
                                )
                            finally:
                                new_loop.close()
                        
                        thread = threading.Thread(target=run_in_thread)
                        thread.start()
                        thread.join()
                        result = result_container.get('result')
                    else:
                        result = loop.run_until_complete(
                            self.mcp_server.execute_tool(tool_name, args)
                        )
                except RuntimeError:
                    # No event loop, create new one
                    result = asyncio.run(self.mcp_server.execute_tool(tool_name, args))
                
                if result.get("success", False):
                    data = result.get("data", [])
                    import json
                    return f"Query successful. Found {len(data)} results: {json.dumps(data, indent=2)}"
                else:
                    return f"Query failed: {result.get('error', 'Unknown error')}"
            except Exception as e:
                logger.error("Tool execution failed", tool=tool_name, error=str(e))
                return f"Error: {str(e)}"
        
        return tool_func
    
    def _create_agent_executor(self) -> AgentExecutor:
        """Create LangChain agent executor."""
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are {self.name}. {self.description}\n\nUse the available tools to answer questions."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create executor
        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )
        
        return executor
    
    async def query(self, query: str, chat_history: Optional[List] = None) -> str:
        """
        Execute a query using the agent.
        
        Args:
            query: Natural language query
            chat_history: Optional chat history
            
        Returns:
            Agent response
        """
        try:
            result = await self.agent_executor.ainvoke({
                "input": query,
                "chat_history": chat_history or []
            })
            
            logger.info("Agent query executed", agent=self.name, query=query)
            return result.get("output", "No response")
            
        except Exception as e:
            logger.error("Agent query failed", agent=self.name, error=str(e))
            return f"Error: {str(e)}"
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools]
