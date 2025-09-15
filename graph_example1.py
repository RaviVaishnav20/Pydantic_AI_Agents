from dataclasses import dataclass
from pydantic_graph import GraphRunContext, BaseNode, Graph, End


@dataclass
class NodeA(BaseNode[int]):
    track_number: int

    async def run(self, ctx: GraphRunContext) -> BaseNode:
        print("Calling Node A")
        print(f"state: {ctx}")
        return NodeB(self.track_number)

@dataclass
class NodeB(BaseNode[int]):
    track_number: int

    async def run(self, ctx: GraphRunContext) -> BaseNode | End:
        print("Calling Node B")
        print(f"state: {ctx}")
        if self.track_number == 1:
            return End(f'Stop at Node B with value --> {self.track_number}')
        else:
            return NodeC(self.track_number)

@dataclass
class NodeC(BaseNode[int]):
    track_number: int

    async def run(self, ctx: GraphRunContext) -> End:
        print("Calling Node C")
        print(f"state: {ctx}")
        return End(f'Stop at Node C with value --> {self.track_number}')

graph = Graph(nodes = [NodeA, NodeB, NodeC])

run_result = graph.run_sync(start_node=NodeA(track_number=4))
print(run_result)
print('#' * 40)
result = run_result.output
print(result)
print('#' * 40)
history = run_result.state
print(history)

# print('#' * 40)
# print('History: ')
# for history_part in history:
#     print(history_part)
#     print()

# print('-' * 40)
# print('Result:', result)