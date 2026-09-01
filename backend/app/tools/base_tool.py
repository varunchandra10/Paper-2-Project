from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """Abstract Base Class for all agentic diagnostic tools."""

    name: str
    description: str

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Executes tool action and returns formatted string output for the LLM."""
        pass

    def run(self, **kwargs) -> str:
        """Safely executes the tool with exception handling."""
        try:
            return self.execute(**kwargs)
        except Exception as e:
            return f"Error executing tool '{self.name}': {str(e)}"
