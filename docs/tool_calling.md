# Tool Calling

Tools implement the `AssistantTool` abstraction:

```python
class AssistantTool:
    name: str
    description: str
    input_schema: dict
    output_schema: dict

    def run(self, input_data: dict) -> dict:
        ...
```

The registry exposes tools by name and makes planner output executable. This keeps agent planning separate from tool implementation.

