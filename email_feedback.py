from __future__ import annotations as __annotatiions
from dataclasses import dataclass, field
from pydantic import BaseModel, EmailStr
from pydantic_ai import Agent
from pydantic_ai import format_as_xml
from pydantic_ai.messages import ModelMessage
from pydantic_graph import BaseNode, End, Graph, GraphRunContext
from load_models import GEMINI_MODEL

@dataclass
class User:
    name: str
    email: EmailStr
    interests: list[str]

@dataclass
class State:
    user: User
    write_agent_messages: list[ModelMessage] = field(default_factory=list)

@dataclass
class Email:
    subject: str
    body: str

class EmailRequiresWrite(BaseModel):
    feedback: str

class EmailOk(BaseModel):
    pass

email_writer_agent = Agent(
    model=GEMINI_MODEL,
    output_type=Email,
    system_prompt='Write a welcome email for the people who subscribe to my tech blog.',
)


feedback_agent = Agent(
    model=GEMINI_MODEL,
    output_type=EmailRequiresWrite | EmailOk,
    system_prompt=(
        'Review the email and provide feedback, email must reference the users specific interests.'
    ),
)

@dataclass
class WriteEmail(BaseNode[State]):
    email_feedback: str | None = None
    async def run(self, ctx: GraphRunContext[State]) -> Feedback:
        print('-'*50)
        print('WriteEmail call fired. Email feedback:', self.email_feedback)
        print()
        if self.email_feedback:
            prompt = (
                f'Rewrite the email for the user:\n'
                f'{format_as_xml(ctx.state.user)}\n'
                f'Feedback: {self.email_feedback}'
            )
        else:
            user_xml = """
            <examples>
                <name>Snowden Sigaba</name>
                <email>snowden.sigaba@example.com</email>
            </examples>
            """
            prompt = (
                f'Write a welcome email for the user:\n'
                f'{user_xml}'
            )
        result = await email_writer_agent.run(
            prompt,
            message_history=ctx.state.write_agent_messages,
        )
        print('WriteEmail result Received. Result:', result.output)
        print('-'*50)

        ctx.state.write_agent_messages += result.all_messages()
        return Feedback(result.output)

@dataclass
class Feedback(BaseNode[State, None, Email]):
    email: Email

    async def run(self, ctx: GraphRunContext[State]) -> WriteEmail | End[Email]:
        print('Feedback call fired. Email object received:', self.email)
        print()

        prompt = format_as_xml({'user': ctx.state.user, 'email': self.email})

        result = await feedback_agent.run(prompt)
        print('Feedback result received. Feedback result:', result.output)
        if isinstance(result.output, EmailRequiresWrite):
            return WriteEmail(email_feedback=result.output.feedback)
        else:
            return End(self.email)


feedback_graph = Graph(nodes=[WriteEmail, Feedback])

user = User(
    name='Jay',
    email='jay@example.com',
    interests=['AI Agent', 'Photography', 'Automation'],
)

state = State(user)

email = feedback_graph.run_sync(WriteEmail(), state=state)
print(email)