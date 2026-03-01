
TAKEN FROM https://ai.pydantic.dev/agent/


Agents
Introduction
Agents are Pydantic AI's primary interface for interacting with LLMs.

In some use cases a single Agent will control an entire application or component, but multiple agents can also interact to embody more complex workflows.

The Agent class has full API documentation, but conceptually you can think of an agent as a container for:

Component	Description
Instructions	A set of instructions for the LLM written by the developer.
Function tool(s) and toolsets	Functions that the LLM may call to get information while generating a response.
Structured output type	The structured datatype the LLM must return at the end of a run, if specified.
Dependency type constraint	Dynamic instructions functions, tools, and output functions may all use dependencies when they're run.
LLM model	Optional default LLM model associated with the agent. Can also be specified when running the agent.
Model Settings	Optional default model settings to help fine tune requests. Can also be specified when running the agent.
In typing terms, agents are generic in their dependency and output types, e.g., an agent which required dependencies of type Foobar and produced outputs of type list[str] would have type Agent[Foobar, list[str]]. In practice, you shouldn't need to care about this, it should just mean your IDE can tell you when you have the right type, and if you choose to use static type checking it should work well with Pydantic AI.

Here's a toy example of an agent that simulates a roulette wheel:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayroulette_wheel.py

from pydantic_ai import Agent, RunContext

roulette_agent = Agent(  
    'gateway/openai:gpt-5.2',
    deps_type=int,
    output_type=bool,
    system_prompt=(
        'Use the `roulette_wheel` function to see if the '
        'customer has won based on the number they provide.'
    ),
)


@roulette_agent.tool
async def roulette_wheel(ctx: RunContext[int], square: int) -> str:  
    """check if the square is a winner"""
    return 'winner' if square == ctx.deps else 'loser'


# Run the agent
success_number = 18  
result = roulette_agent.run_sync('Put my money on square eighteen', deps=success_number)
print(result.output)  
#> True

result = roulette_agent.run_sync('I bet five is the winner', deps=success_number)
print(result.output)
#> False

Agents are designed for reuse, like FastAPI Apps

You can instantiate one agent and use it globally throughout your application, as you would a small FastAPI app or an APIRouter, or dynamically create as many agents as you want. Both are valid and supported ways to use agents.

Running Agents
There are five ways to run an agent:

agent.run() — an async function which returns a RunResult containing a completed response.
agent.run_sync() — a plain, synchronous function which returns a RunResult containing a completed response (internally, this just calls loop.run_until_complete(self.run())).
agent.run_stream() — an async context manager which returns a StreamedRunResult, which contains methods to stream text and structured output as an async iterable. agent.run_stream_sync() is a synchronous variation that returns a StreamedRunResultSync with synchronous versions of the same methods.
agent.run_stream_events() — a function which returns an async iterable of AgentStreamEvents and a AgentRunResultEvent containing the final run result.
agent.iter() — a context manager which returns an AgentRun, an async iterable over the nodes of the agent's underlying Graph.
Here's a simple example demonstrating the first four:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayrun_agent.py

from pydantic_ai import Agent, AgentRunResultEvent, AgentStreamEvent

agent = Agent('gateway/openai:gpt-5.2')

result_sync = agent.run_sync('What is the capital of Italy?')
print(result_sync.output)
#> The capital of Italy is Rome.


async def main():
    result = await agent.run('What is the capital of France?')
    print(result.output)
    #> The capital of France is Paris.

    async with agent.run_stream('What is the capital of the UK?') as response:
        async for text in response.stream_text():
            print(text)
            #> The capital of
            #> The capital of the UK is
            #> The capital of the UK is London.

    events: list[AgentStreamEvent | AgentRunResultEvent] = []
    async for event in agent.run_stream_events('What is the capital of Mexico?'):
        events.append(event)
    print(events)
    """
    [
        PartStartEvent(index=0, part=TextPart(content='The capital of ')),
        FinalResultEvent(tool_name=None, tool_call_id=None),
        PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='Mexico is Mexico ')),
        PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='City.')),
        PartEndEvent(
            index=0, part=TextPart(content='The capital of Mexico is Mexico City.')
        ),
        AgentRunResultEvent(
            result=AgentRunResult(output='The capital of Mexico is Mexico City.')
        ),
    ]
    """

(This example is complete, it can be run "as is" — you'll need to add asyncio.run(main()) to run main)

You can also pass messages from previous runs to continue a conversation or provide context, as described in Messages and Chat History.

Streaming Events and Final Output
As shown in the example above, run_stream() makes it easy to stream the agent's final output as it comes in. It also takes an optional event_stream_handler argument that you can use to gain insight into what is happening during the run before the final output is produced.

The example below shows how to stream events and text output. You can also stream structured output.

Note

The run_stream() and run_stream_sync() methods will consider the first output that matches the output type (which could be text, an output tool call, or a deferred tool call) to be the final output of the agent run, even when the model generates (additional) tool calls after this "final" output.

These "dangling" tool calls will not be executed unless the agent's end_strategy is set to 'exhaustive', and even then their results will not be sent back to the model as the agent run will already be considered completed. In short, if the model returns both tool calls and text, and the agent's output type is str, the tool calls will not run in streaming mode with the default setting.

If you want to always keep running the agent when it performs tool calls, and stream all events from the model's streaming response and the agent's execution of tools, use agent.run_stream_events() or agent.iter() instead, as described in the following sections.


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayrun_stream_event_stream_handler.py

import asyncio
from collections.abc import AsyncIterable
from datetime import date

from pydantic_ai import (
    Agent,
    AgentStreamEvent,
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    RunContext,
    TextPartDelta,
    ThinkingPartDelta,
    ToolCallPartDelta,
)

weather_agent = Agent(
    'gateway/openai:gpt-5.2',
    system_prompt='Providing a weather forecast at the locations the user provides.',
)


@weather_agent.tool
async def weather_forecast(
    ctx: RunContext,
    location: str,
    forecast_date: date,
) -> str:
    return f'The forecast in {location} on {forecast_date} is 24°C and sunny.'


output_messages: list[str] = []

async def handle_event(event: AgentStreamEvent):
    if isinstance(event, PartStartEvent):
        output_messages.append(f'[Request] Starting part {event.index}: {event.part!r}')
    elif isinstance(event, PartDeltaEvent):
        if isinstance(event.delta, TextPartDelta):
            output_messages.append(f'[Request] Part {event.index} text delta: {event.delta.content_delta!r}')
        elif isinstance(event.delta, ThinkingPartDelta):
            output_messages.append(f'[Request] Part {event.index} thinking delta: {event.delta.content_delta!r}')
        elif isinstance(event.delta, ToolCallPartDelta):
            output_messages.append(f'[Request] Part {event.index} args delta: {event.delta.args_delta}')
    elif isinstance(event, FunctionToolCallEvent):
        output_messages.append(
            f'[Tools] The LLM calls tool={event.part.tool_name!r} with args={event.part.args} (tool_call_id={event.part.tool_call_id!r})'
        )
    elif isinstance(event, FunctionToolResultEvent):
        output_messages.append(f'[Tools] Tool call {event.tool_call_id!r} returned => {event.result.content}')
    elif isinstance(event, FinalResultEvent):
        output_messages.append(f'[Result] The model starting producing a final result (tool_name={event.tool_name})')


async def event_stream_handler(
    ctx: RunContext,
    event_stream: AsyncIterable[AgentStreamEvent],
):
    async for event in event_stream:
        await handle_event(event)

async def main():
    user_prompt = 'What will the weather be like in Paris on Tuesday?'

    async with weather_agent.run_stream(user_prompt, event_stream_handler=event_stream_handler) as run:
        async for output in run.stream_text():
            output_messages.append(f'[Output] {output}')


if __name__ == '__main__':
    asyncio.run(main())

    print(output_messages)
    """
    [
        "[Request] Starting part 0: ToolCallPart(tool_name='weather_forecast', tool_call_id='0001')",
        '[Request] Part 0 args delta: {"location":"Pa',
        '[Request] Part 0 args delta: ris","forecast_',
        '[Request] Part 0 args delta: date":"2030-01-',
        '[Request] Part 0 args delta: 01"}',
        '[Tools] The LLM calls tool=\'weather_forecast\' with args={"location":"Paris","forecast_date":"2030-01-01"} (tool_call_id=\'0001\')',
        "[Tools] Tool call '0001' returned => The forecast in Paris on 2030-01-01 is 24°C and sunny.",
        "[Request] Starting part 0: TextPart(content='It will be ')",
        '[Result] The model starting producing a final result (tool_name=None)',
        '[Output] It will be ',
        '[Output] It will be warm and sunny ',
        '[Output] It will be warm and sunny in Paris on ',
        '[Output] It will be warm and sunny in Paris on Tuesday.',
    ]
    """

(This example is complete, it can be run "as is")

Streaming All Events
Like agent.run_stream(), agent.run() takes an optional event_stream_handler argument that lets you stream all events from the model's streaming response and the agent's execution of tools. Unlike run_stream(), it always runs the agent graph to completion even if text was received ahead of tool calls that looked like it could've been the final result.

For convenience, a agent.run_stream_events() method is also available as a wrapper around run(event_stream_handler=...), which returns an async iterable of AgentStreamEvents and a AgentRunResultEvent containing the final run result.

Note

As they return raw events as they come in, the run_stream_events() and run(event_stream_handler=...) methods require you to piece together the streamed text and structured output yourself from the PartStartEvent and subsequent PartDeltaEvents.

To get the best of both worlds, at the expense of some additional complexity, you can use agent.iter() as described in the next section, which lets you iterate over the agent graph and stream both events and output at every step.

run_events.py

import asyncio

from pydantic_ai import AgentRunResultEvent

from run_stream_event_stream_handler import handle_event, output_messages, weather_agent


async def main():
    user_prompt = 'What will the weather be like in Paris on Tuesday?'

    async for event in weather_agent.run_stream_events(user_prompt):
        if isinstance(event, AgentRunResultEvent):
            output_messages.append(f'[Final Output] {event.result.output}')
        else:
            await handle_event(event)

if __name__ == '__main__':
    asyncio.run(main())

    print(output_messages)
    """
    [
        "[Request] Starting part 0: ToolCallPart(tool_name='weather_forecast', tool_call_id='0001')",
        '[Request] Part 0 args delta: {"location":"Pa',
        '[Request] Part 0 args delta: ris","forecast_',
        '[Request] Part 0 args delta: date":"2030-01-',
        '[Request] Part 0 args delta: 01"}',
        '[Tools] The LLM calls tool=\'weather_forecast\' with args={"location":"Paris","forecast_date":"2030-01-01"} (tool_call_id=\'0001\')',
        "[Tools] Tool call '0001' returned => The forecast in Paris on 2030-01-01 is 24°C and sunny.",
        "[Request] Starting part 0: TextPart(content='It will be ')",
        '[Result] The model starting producing a final result (tool_name=None)',
        "[Request] Part 0 text delta: 'warm and sunny '",
        "[Request] Part 0 text delta: 'in Paris on '",
        "[Request] Part 0 text delta: 'Tuesday.'",
        '[Final Output] It will be warm and sunny in Paris on Tuesday.',
    ]
    """
(This example is complete, it can be run "as is")

Iterating Over an Agent's Graph
Under the hood, each Agent in Pydantic AI uses pydantic-graph to manage its execution flow. pydantic-graph is a generic, type-centric library for building and running finite state machines in Python. It doesn't actually depend on Pydantic AI — you can use it standalone for workflows that have nothing to do with GenAI — but Pydantic AI makes use of it to orchestrate the handling of model requests and model responses in an agent's run.

In many scenarios, you don't need to worry about pydantic-graph at all; calling agent.run(...) simply traverses the underlying graph from start to finish. However, if you need deeper insight or control — for example to inject your own logic at specific stages — Pydantic AI exposes the lower-level iteration process via Agent.iter. This method returns an AgentRun, which you can async-iterate over, or manually drive node-by-node via the next method. Once the agent's graph returns an End, you have the final result along with a detailed history of all steps.

async for iteration
Here's an example of using async for with iter to record each node the agent executes:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayagent_iter_async_for.py

from pydantic_ai import Agent

agent = Agent('gateway/openai:gpt-5.2')


async def main():
    nodes = []
    # Begin an AgentRun, which is an async-iterable over the nodes of the agent's graph
    async with agent.iter('What is the capital of France?') as agent_run:
        async for node in agent_run:
            # Each node represents a step in the agent's execution
            nodes.append(node)
    print(nodes)
    """
    [
        UserPromptNode(
            user_prompt='What is the capital of France?',
            instructions_functions=[],
            system_prompts=(),
            system_prompt_functions=[],
            system_prompt_dynamic_functions={},
        ),
        ModelRequestNode(
            request=ModelRequest(
                parts=[
                    UserPromptPart(
                        content='What is the capital of France?',
                        timestamp=datetime.datetime(...),
                    )
                ],
                timestamp=datetime.datetime(...),
                run_id='...',
            )
        ),
        CallToolsNode(
            model_response=ModelResponse(
                parts=[TextPart(content='The capital of France is Paris.')],
                usage=RequestUsage(input_tokens=56, output_tokens=7),
                model_name='gpt-5.2',
                timestamp=datetime.datetime(...),
                run_id='...',
            )
        ),
        End(data=FinalResult(output='The capital of France is Paris.')),
    ]
    """
    print(agent_run.result.output)
    #> The capital of France is Paris.

(This example is complete, it can be run "as is" — you'll need to add asyncio.run(main()) to run main)

The AgentRun is an async iterator that yields each node (BaseNode or End) in the flow.
The run ends when an End node is returned.
Using .next(...) manually
You can also drive the iteration manually by passing the node you want to run next to the AgentRun.next(...) method. This allows you to inspect or modify the node before it executes or skip nodes based on your own logic, and to catch errors in next() more easily:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayagent_iter_next.py

from pydantic_ai import Agent
from pydantic_graph import End

agent = Agent('gateway/openai:gpt-5.2')


async def main():
    async with agent.iter('What is the capital of France?') as agent_run:
        node = agent_run.next_node  

        all_nodes = [node]

        # Drive the iteration manually:
        while not isinstance(node, End):  
            node = await agent_run.next(node)  
            all_nodes.append(node)  

        print(all_nodes)
        """
        [
            UserPromptNode(
                user_prompt='What is the capital of France?',
                instructions_functions=[],
                system_prompts=(),
                system_prompt_functions=[],
                system_prompt_dynamic_functions={},
            ),
            ModelRequestNode(
                request=ModelRequest(
                    parts=[
                        UserPromptPart(
                            content='What is the capital of France?',
                            timestamp=datetime.datetime(...),
                        )
                    ],
                    timestamp=datetime.datetime(...),
                    run_id='...',
                )
            ),
            CallToolsNode(
                model_response=ModelResponse(
                    parts=[TextPart(content='The capital of France is Paris.')],
                    usage=RequestUsage(input_tokens=56, output_tokens=7),
                    model_name='gpt-5.2',
                    timestamp=datetime.datetime(...),
                    run_id='...',
                )
            ),
            End(data=FinalResult(output='The capital of France is Paris.')),
        ]
        """

(This example is complete, it can be run "as is" — you'll need to add asyncio.run(main()) to run main)

Accessing usage and final output
You can retrieve usage statistics (tokens, requests, etc.) at any time from the AgentRun object via agent_run.usage(). This method returns a RunUsage object containing the usage data.

Once the run finishes, agent_run.result becomes an AgentRunResult object containing the final output (and related metadata).

Streaming All Events and Output
Here is an example of streaming an agent run in combination with async for iteration:

streaming_iter.py

import asyncio
from dataclasses import dataclass
from datetime import date

from pydantic_ai import (
    Agent,
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    RunContext,
    TextPartDelta,
    ThinkingPartDelta,
    ToolCallPartDelta,
)


@dataclass
class WeatherService:
    async def get_forecast(self, location: str, forecast_date: date) -> str:
        # In real code: call weather API, DB queries, etc.
        return f'The forecast in {location} on {forecast_date} is 24°C and sunny.'

    async def get_historic_weather(self, location: str, forecast_date: date) -> str:
        # In real code: call a historical weather API or DB
        return f'The weather in {location} on {forecast_date} was 18°C and partly cloudy.'


weather_agent = Agent[WeatherService, str](
    'openai:gpt-5.2',
    deps_type=WeatherService,
    output_type=str,  # We'll produce a final answer as plain text
    system_prompt='Providing a weather forecast at the locations the user provides.',
)


@weather_agent.tool
async def weather_forecast(
    ctx: RunContext[WeatherService],
    location: str,
    forecast_date: date,
) -> str:
    if forecast_date >= date.today():
        return await ctx.deps.get_forecast(location, forecast_date)
    else:
        return await ctx.deps.get_historic_weather(location, forecast_date)


output_messages: list[str] = []


async def main():
    user_prompt = 'What will the weather be like in Paris on Tuesday?'

    # Begin a node-by-node, streaming iteration
    async with weather_agent.iter(user_prompt, deps=WeatherService()) as run:
        async for node in run:
            if Agent.is_user_prompt_node(node):
                # A user prompt node => The user has provided input
                output_messages.append(f'=== UserPromptNode: {node.user_prompt} ===')
            elif Agent.is_model_request_node(node):
                # A model request node => We can stream tokens from the model's request
                output_messages.append('=== ModelRequestNode: streaming partial request tokens ===')
                async with node.stream(run.ctx) as request_stream:
                    final_result_found = False
                    async for event in request_stream:
                        if isinstance(event, PartStartEvent):
                            output_messages.append(f'[Request] Starting part {event.index}: {event.part!r}')
                        elif isinstance(event, PartDeltaEvent):
                            if isinstance(event.delta, TextPartDelta):
                                output_messages.append(
                                    f'[Request] Part {event.index} text delta: {event.delta.content_delta!r}'
                                )
                            elif isinstance(event.delta, ThinkingPartDelta):
                                output_messages.append(
                                    f'[Request] Part {event.index} thinking delta: {event.delta.content_delta!r}'
                                )
                            elif isinstance(event.delta, ToolCallPartDelta):
                                output_messages.append(
                                    f'[Request] Part {event.index} args delta: {event.delta.args_delta}'
                                )
                        elif isinstance(event, FinalResultEvent):
                            output_messages.append(
                                f'[Result] The model started producing a final result (tool_name={event.tool_name})'
                            )
                            final_result_found = True
                            break

                    if final_result_found:
                        # Once the final result is found, we can call `AgentStream.stream_text()` to stream the text.
                        # A similar `AgentStream.stream_output()` method is available to stream structured output.
                        async for output in request_stream.stream_text():
                            output_messages.append(f'[Output] {output}')
            elif Agent.is_call_tools_node(node):
                # A handle-response node => The model returned some data, potentially calls a tool
                output_messages.append('=== CallToolsNode: streaming partial response & tool usage ===')
                async with node.stream(run.ctx) as handle_stream:
                    async for event in handle_stream:
                        if isinstance(event, FunctionToolCallEvent):
                            output_messages.append(
                                f'[Tools] The LLM calls tool={event.part.tool_name!r} with args={event.part.args} (tool_call_id={event.part.tool_call_id!r})'
                            )
                        elif isinstance(event, FunctionToolResultEvent):
                            output_messages.append(
                                f'[Tools] Tool call {event.tool_call_id!r} returned => {event.result.content}'
                            )
            elif Agent.is_end_node(node):
                # Once an End node is reached, the agent run is complete
                assert run.result is not None
                assert run.result.output == node.data.output
                output_messages.append(f'=== Final Agent Output: {run.result.output} ===')


if __name__ == '__main__':
    asyncio.run(main())

    print(output_messages)
    """
    [
        '=== UserPromptNode: What will the weather be like in Paris on Tuesday? ===',
        '=== ModelRequestNode: streaming partial request tokens ===',
        "[Request] Starting part 0: ToolCallPart(tool_name='weather_forecast', tool_call_id='0001')",
        '[Request] Part 0 args delta: {"location":"Pa',
        '[Request] Part 0 args delta: ris","forecast_',
        '[Request] Part 0 args delta: date":"2030-01-',
        '[Request] Part 0 args delta: 01"}',
        '=== CallToolsNode: streaming partial response & tool usage ===',
        '[Tools] The LLM calls tool=\'weather_forecast\' with args={"location":"Paris","forecast_date":"2030-01-01"} (tool_call_id=\'0001\')',
        "[Tools] Tool call '0001' returned => The forecast in Paris on 2030-01-01 is 24°C and sunny.",
        '=== ModelRequestNode: streaming partial request tokens ===',
        "[Request] Starting part 0: TextPart(content='It will be ')",
        '[Result] The model started producing a final result (tool_name=None)',
        '[Output] It will be ',
        '[Output] It will be warm and sunny ',
        '[Output] It will be warm and sunny in Paris on ',
        '[Output] It will be warm and sunny in Paris on Tuesday.',
        '=== CallToolsNode: streaming partial response & tool usage ===',
        '=== Final Agent Output: It will be warm and sunny in Paris on Tuesday. ===',
    ]
    """
(This example is complete, it can be run "as is")

Additional Configuration
Usage Limits
Pydantic AI offers a UsageLimits structure to help you limit your usage (tokens, requests, and tool calls) on model runs.

You can apply these settings by passing the usage_limits argument to the run{_sync,_stream} functions.

Consider the following example, where we limit the number of response tokens:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gateway

from pydantic_ai import Agent, UsageLimitExceeded, UsageLimits

agent = Agent('gateway/anthropic:claude-sonnet-4-6')

result_sync = agent.run_sync(
    'What is the capital of Italy? Answer with just the city.',
    usage_limits=UsageLimits(response_tokens_limit=10),
)
print(result_sync.output)
#> Rome
print(result_sync.usage())
#> RunUsage(input_tokens=62, output_tokens=1, requests=1)

try:
    result_sync = agent.run_sync(
        'What is the capital of Italy? Answer with a paragraph.',
        usage_limits=UsageLimits(response_tokens_limit=10),
    )
except UsageLimitExceeded as e:
    print(e)
    #> Exceeded the output_tokens_limit of 10 (output_tokens=32)

Restricting the number of requests can be useful in preventing infinite loops or excessive tool calling:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gateway

from typing_extensions import TypedDict

from pydantic_ai import Agent, ModelRetry, UsageLimitExceeded, UsageLimits


class NeverOutputType(TypedDict):
    """
    Never ever coerce data to this type.
    """

    never_use_this: str


agent = Agent(
    'gateway/anthropic:claude-sonnet-4-6',
    retries=3,
    output_type=NeverOutputType,
    system_prompt='Any time you get a response, call the `infinite_retry_tool` to produce another response.',
)


@agent.tool_plain(retries=5)  
def infinite_retry_tool() -> int:
    raise ModelRetry('Please try again.')


try:
    result_sync = agent.run_sync(
        'Begin infinite retry loop!', usage_limits=UsageLimits(request_limit=3)  
    )
except UsageLimitExceeded as e:
    print(e)
    #> The next request would exceed the request_limit of 3

Capping tool calls
If you need a limit on the number of successful tool invocations within a single run, use tool_calls_limit:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gateway

from pydantic_ai import Agent
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.usage import UsageLimits

agent = Agent('gateway/anthropic:claude-sonnet-4-6')

@agent.tool_plain
def do_work() -> str:
    return 'ok'

try:
    # Allow at most one executed tool call in this run
    agent.run_sync('Please call the tool twice', usage_limits=UsageLimits(tool_calls_limit=1))
except UsageLimitExceeded as e:
    print(e)
    #> The next tool call(s) would exceed the tool_calls_limit of 1 (tool_calls=2).

Note

Usage limits are especially relevant if you've registered many tools. Use request_limit to bound the number of model turns, and tool_calls_limit to cap the number of successful tool executions within a run.
The tool_calls_limit is checked before executing tool calls. If the model returns parallel tool calls that would exceed the limit, no tools will be executed.
Model (Run) Settings
Pydantic AI offers a settings.ModelSettings structure to help you fine tune your requests. This structure allows you to configure common parameters that influence the model's behavior, such as temperature, max_tokens, timeout, and more.

There are three ways to apply these settings, with a clear precedence order:

Model-level defaults - Set when creating a model instance via the settings parameter. These serve as the base defaults for that model.
Agent-level defaults - Set during Agent initialization via the model_settings argument. These are merged with model defaults, with agent settings taking precedence.
Run-time overrides - Passed to run{_sync,_stream} functions via the model_settings argument. These have the highest priority and are merged with the combined agent and model defaults.
For example, if you'd like to set the temperature setting to 0.0 to ensure less random behavior, you can do the following:


from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel

# 1. Model-level defaults
model = OpenAIChatModel(
    'gpt-5.2',
    settings=ModelSettings(temperature=0.8, max_tokens=500)  # Base defaults
)

# 2. Agent-level defaults (overrides model defaults by merging)
agent = Agent(model, model_settings=ModelSettings(temperature=0.5))

# 3. Run-time overrides (highest priority)
result_sync = agent.run_sync(
    'What is the capital of Italy?',
    model_settings=ModelSettings(temperature=0.0)  # Final temperature: 0.0
)
print(result_sync.output)
#> The capital of Italy is Rome.
The final request uses temperature=0.0 (run-time), max_tokens=500 (from model), demonstrating how settings merge with run-time taking precedence.

Model Settings Support

Model-level settings are supported by all concrete model implementations (OpenAI, Anthropic, Google, etc.). Wrapper models like FallbackModel, WrapperModel, and InstrumentedModel don't have their own settings - they use the settings of their underlying models.

Run metadata
Run metadata lets you tag each agent execution with contextual details (for example, a tenant ID to filter traces and logs) and read it after completion via AgentRun.metadata, AgentRunResult.metadata, or StreamedRunResult.metadata. The resolved metadata is attached to the RunContext during the run and, when instrumentation is enabled, added to the run span attributes for observability tools.

Configure metadata on an Agent or pass it to a run. Both accept either a static dictionary or a callable that receives the RunContext. Metadata is computed (if a callable) and applied when the run starts, then recomputed after a run ends successfully, so it can include end-of-run values. Agent-level metadata and per-run metadata are merged, with per-run values overriding agent-level ones.

run_metadata.py

from dataclasses import dataclass

from pydantic_ai import Agent


@dataclass
class Deps:
    tenant: str


agent = Agent[Deps](
    'openai:gpt-5.2',
    deps_type=Deps,
    metadata=lambda ctx: {'tenant': ctx.deps.tenant},  # agent-level metadata
)

result = agent.run_sync(
    'What is the capital of France?',
    deps=Deps(tenant='tenant-123'),
    metadata=lambda ctx: {'num_requests': ctx.usage.requests},  # per-run metadata
)
print(result.output)
#> The capital of France is Paris.
print(result.metadata)
#> {'tenant': 'tenant-123', 'num_requests': 1}
Concurrency Limiting
You can limit the number of concurrent agent runs using the max_concurrency parameter. This is useful when you want to prevent overwhelming external resources or enforce rate limits when running many agent instances in parallel.


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayagent_concurrency.py

import asyncio

from pydantic_ai import Agent, ConcurrencyLimit

# Simple limit: allow up to 10 concurrent runs
agent = Agent('gateway/openai:gpt-5', max_concurrency=10)


# With backpressure: limit concurrent runs and queue depth
agent_with_backpressure = Agent(
    'gateway/openai:gpt-5',
    max_concurrency=ConcurrencyLimit(max_running=10, max_queued=100),
)


async def main():
    # These will be rate-limited to 10 concurrent runs
    results = await asyncio.gather(
        *[agent.run(f'Question {i}') for i in range(20)]
    )
    print(len(results))
    #> 20

When the concurrency limit is reached, additional calls to agent.run() or agent.iter() will wait until a slot becomes available. If you configure max_queued and the queue fills up, a ConcurrencyLimitExceeded exception is raised.

When instrumentation is enabled, waiting operations appear as "waiting for concurrency" spans with attributes showing queue depth and limits.

Model specific settings
If you wish to further customize model behavior, you can use a subclass of ModelSettings, like GoogleModelSettings, associated with your model of choice.

For example:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gateway

from pydantic_ai import Agent, UnexpectedModelBehavior
from pydantic_ai.models.google import GoogleModelSettings

agent = Agent('gateway/gemini:gemini-3-flash-preview')

try:
    result = agent.run_sync(
        'Write a list of 5 very rude things that I might say to the universe after stubbing my toe in the dark:',
        model_settings=GoogleModelSettings(
            temperature=0.0,  # general model settings can also be specified
            gemini_safety_settings=[
                {
                    'category': 'HARM_CATEGORY_HARASSMENT',
                    'threshold': 'BLOCK_LOW_AND_ABOVE',
                },
                {
                    'category': 'HARM_CATEGORY_HATE_SPEECH',
                    'threshold': 'BLOCK_LOW_AND_ABOVE',
                },
            ],
        ),
    )
except UnexpectedModelBehavior as e:
    print(e)  
    """
    Content filter 'SAFETY' triggered, body:
    <safety settings details>
    """

Runs vs. Conversations
An agent run might represent an entire conversation — there's no limit to how many messages can be exchanged in a single run. However, a conversation might also be composed of multiple runs, especially if you need to maintain state between separate interactions or API calls.

Here's an example of a conversation comprised of multiple runs:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayconversation_example.py

from pydantic_ai import Agent

agent = Agent('gateway/openai:gpt-5.2')

# First run
result1 = agent.run_sync('Who was Albert Einstein?')
print(result1.output)
#> Albert Einstein was a German-born theoretical physicist.

# Second run, passing previous messages
result2 = agent.run_sync(
    'What was his most famous equation?',
    message_history=result1.new_messages(),  
)
print(result2.output)
#> Albert Einstein's most famous equation is (E = mc^2).

(This example is complete, it can be run "as is")

Type safe by design
Pydantic AI is designed to work well with static type checkers, like mypy and pyright.

Typing is (somewhat) optional

Pydantic AI is designed to make type checking as useful as possible for you if you choose to use it, but you don't have to use types everywhere all the time.

That said, because Pydantic AI uses Pydantic, and Pydantic uses type hints as the definition for schema and validation, some types (specifically type hints on parameters to tools, and the output_type arguments to Agent) are used at runtime.

We (the library developers) have messed up if type hints are confusing you more than helping you, if you find this, please create an issue explaining what's annoying you!

In particular, agents are generic in both the type of their dependencies and the type of the outputs they return, so you can use the type hints to ensure you're using the right types.

Consider the following script with type mistakes:

type_mistakes.py

from dataclasses import dataclass

from pydantic_ai import Agent, RunContext


@dataclass
class User:
    name: str


agent = Agent(
    'test',
    deps_type=User,  
    output_type=bool,
)


@agent.system_prompt
def add_user_name(ctx: RunContext[str]) -> str:  
    return f"The user's name is {ctx.deps}."


def foobar(x: bytes) -> None:
    pass


result = agent.run_sync('Does their name start with "A"?', deps=User('Anne'))
foobar(result.output)  
Running mypy on this will give the following output:


➤ uv run mypy type_mistakes.py
type_mistakes.py:18: error: Argument 1 to "system_prompt" of "Agent" has incompatible type "Callable[[RunContext[str]], str]"; expected "Callable[[RunContext[User]], str]"  [arg-type]
type_mistakes.py:28: error: Argument 1 to "foobar" has incompatible type "bool"; expected "bytes"  [arg-type]
Found 2 errors in 1 file (checked 1 source file)
Running pyright would identify the same issues.

System Prompts
System prompts might seem simple at first glance since they're just strings (or sequences of strings that are concatenated), but crafting the right system prompt is key to getting the model to behave as you want.

Tip

For most use cases, you should use instructions instead of "system prompts".

If you know what you are doing though and want to preserve system prompt messages in the message history sent to the LLM in subsequent completions requests, you can achieve this using the system_prompt argument/decorator.

See the section below on Instructions for more information.

Generally, system prompts fall into two categories:

Static system prompts: These are known when writing the code and can be defined via the system_prompt parameter of the Agent constructor.
Dynamic system prompts: These depend in some way on context that isn't known until runtime, and should be defined via functions decorated with @agent.system_prompt.
You can add both to a single agent; they're appended in the order they're defined at runtime.

Here's an example using both types of system prompts:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaysystem_prompts.py

from datetime import date

from pydantic_ai import Agent, RunContext

agent = Agent(
    'gateway/openai:gpt-5.2',
    deps_type=str,  
    system_prompt="Use the customer's name while replying to them.",  
)


@agent.system_prompt  
def add_the_users_name(ctx: RunContext[str]) -> str:
    return f"The user's name is {ctx.deps}."


@agent.system_prompt
def add_the_date() -> str:  
    return f'The date is {date.today()}.'


result = agent.run_sync('What is the date?', deps='Frank')
print(result.output)
#> Hello Frank, the date today is 2032-01-02.

(This example is complete, it can be run "as is")

Instructions
Instructions are similar to system prompts. The main difference is that when an explicit message_history is provided in a call to Agent.run and similar methods, instructions from any existing messages in the history are not included in the request to the model — only the instructions of the current agent are included.

You should use:

instructions when you want your request to the model to only include system prompts for the current agent
system_prompt when you want your request to the model to retain the system prompts used in previous requests (possibly made using other agents)
In general, we recommend using instructions instead of system_prompt unless you have a specific reason to use system_prompt.

Instructions, like system prompts, can be specified at different times:

Static instructions: These are known when writing the code and can be defined via the instructions parameter of the Agent constructor.
Dynamic instructions: These rely on context that is only available at runtime and should be defined using functions decorated with @agent.instructions. Unlike dynamic system prompts, which may be reused when message_history is present, dynamic instructions are always reevaluated.
Runtime instructions: These are additional instructions for a specific run that can be passed to one of the run methods using the instructions argument.
All three types of instructions can be added to a single agent, and they are appended in the order they are defined at runtime.

Here's an example using a static instruction as well as dynamic instructions:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayinstructions.py

from datetime import date

from pydantic_ai import Agent, RunContext

agent = Agent(
    'gateway/openai:gpt-5.2',
    deps_type=str,  
    instructions="Use the customer's name while replying to them.",  
)


@agent.instructions  
def add_the_users_name(ctx: RunContext[str]) -> str:
    return f"The user's name is {ctx.deps}."


@agent.instructions
def add_the_date() -> str:  
    return f'The date is {date.today()}.'


result = agent.run_sync('What is the date?', deps='Frank')
print(result.output)
#> Hello Frank, the date today is 2032-01-02.

(This example is complete, it can be run "as is")

Note that returning an empty string will result in no instruction message added.

Reflection and self-correction
Validation errors from both function tool parameter validation and structured output validation can be passed back to the model with a request to retry.

You can also raise ModelRetry from within a tool or output function to tell the model it should retry generating a response.

The default retry count is 1 but can be altered for the entire agent, a specific tool, or outputs.
You can access the current retry count from within a tool, output validator, or output function via ctx.retry.
Here's an example:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaytool_retry.py

from pydantic import BaseModel

from pydantic_ai import Agent, RunContext, ModelRetry

from fake_database import DatabaseConn


class ChatResult(BaseModel):
    user_id: int
    message: str


agent = Agent(
    'gateway/openai:gpt-5.2',
    deps_type=DatabaseConn,
    output_type=ChatResult,
)


@agent.tool(retries=2)
def get_user_by_name(ctx: RunContext[DatabaseConn], name: str) -> int:
    """Get a user's ID from their full name."""
    print(name)
    #> John
    #> John Doe
    user_id = ctx.deps.users.get(name=name)
    if user_id is None:
        raise ModelRetry(
            f'No user found with name {name!r}, remember to provide their full name'
        )
    return user_id


result = agent.run_sync(
    'Send a message to John Doe asking for coffee next week', deps=DatabaseConn()
)
print(result.output)
"""
user_id=123 message='Hello John, would you be free for coffee sometime next week? Let me know what works for you!'
"""

Debugging and Monitoring
Agents require a different approach to observability than traditional software. With traditional web endpoints or data pipelines, you can largely predict behavior by reading the code. With agents, this is much harder. The model's decisions are stochastic, and that stochasticity compounds through the agentic loop as the agent reasons, calls tools, observes results, and reasons again. You need to actually see what happened.

This means setting up your application to record what's happening in a way you can review afterward, both during development (to understand and iterate) and in production (to debug issues and monitor behavior). The ergonomics matter too: a plaintext dump of everything that happened isn't a practical way to review agent behavior, even during development. You want tooling that lets you step through each decision and tool call interactively.

We recommend Pydantic Logfire, which has been designed with Pydantic AI workflows in mind.

Tracing with Logfire

import logfire

logfire.configure()
logfire.instrument_pydantic_ai()
With Logfire instrumentation enabled, every agent run creates a detailed trace showing:

Messages exchanged with the model (system, user, assistant)
Tool calls including arguments and return values
Token usage per request and cumulative
Latency for each operation
Errors with full context
This visibility is invaluable for:

Understanding why an agent made a specific decision
Debugging unexpected behavior
Optimizing performance and costs
Monitoring production deployments
Systematic Testing with Evals
For systematic evaluation of agent behavior beyond runtime debugging, Pydantic Evals provides a code-first framework for testing AI systems:


from pydantic_evals import Case, Dataset

dataset = Dataset(
    cases=[
        Case(name='capital_question', inputs='What is the capital of France?', expected_output='Paris'),
    ]
)
report = dataset.evaluate_sync(my_agent_function)
Evals let you define test cases, run them against your agent, and score the results. When combined with Logfire, evaluation results appear in the web UI for visualization and comparison across runs. See the Logfire integration guide for setup.

Using Other Backends
Pydantic AI's instrumentation is built on OpenTelemetry, so you can send traces to any compatible backend. Even if you use the Logfire SDK for its convenience, you can configure it to send data to other backends. See alternative backends for setup instructions.

Full Logfire integration guide →

Model errors
If models behave unexpectedly (e.g., the retry limit is exceeded, or their API returns 503), agent runs will raise UnexpectedModelBehavior.

In these cases, capture_run_messages can be used to access the messages exchanged during the run to help diagnose the issue.


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayagent_model_errors.py

from pydantic_ai import Agent, ModelRetry, UnexpectedModelBehavior, capture_run_messages

agent = Agent('gateway/openai:gpt-5.2')


@agent.tool_plain
def calc_volume(size: int) -> int:  
    if size == 42:
        return size**3
    else:
        raise ModelRetry('Please try again.')


with capture_run_messages() as messages:  
    try:
        result = agent.run_sync('Please get me the volume of a box with size 6.')
    except UnexpectedModelBehavior as e:
        print('An error occurred:', e)
        #> An error occurred: Tool 'calc_volume' exceeded max retries count of 1
        print('cause:', repr(e.__cause__))
        #> cause: ModelRetry('Please try again.')
        print('messages:', messages)
        """
        messages:
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='Please get me the volume of a box with size 6.',
                        timestamp=datetime.datetime(...),
                    )
                ],
                timestamp=datetime.datetime(...),
                run_id='...',
            ),
            ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name='calc_volume',
                        args={'size': 6},
                        tool_call_id='pyd_ai_tool_call_id',
                    )
                ],
                usage=RequestUsage(input_tokens=62, output_tokens=4),
                model_name='gpt-5.2',
                timestamp=datetime.datetime(...),
                run_id='...',
            ),
            ModelRequest(
                parts=[
                    RetryPromptPart(
                        content='Please try again.',
                        tool_name='calc_volume',
                        tool_call_id='pyd_ai_tool_call_id',
                        timestamp=datetime.datetime(...),
                    )
                ],
                timestamp=datetime.datetime(...),
                run_id='...',
            ),
            ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name='calc_volume',
                        args={'size': 6},
                        tool_call_id='pyd_ai_tool_call_id',
                    )
                ],
                usage=RequestUsage(input_tokens=72, output_tokens=8),
                model_name='gpt-5.2',
                timestamp=datetime.datetime(...),
                run_id='...',
            ),
        ]
        """
    else:
        print(result.output)

        Pydantic AI
Documentation
Core Concepts
Dependencies
Pydantic AI uses a dependency injection system to provide data and services to your agent's system prompts, tools and output validators.

Matching Pydantic AI's design philosophy, our dependency system tries to use existing best practice in Python development rather than inventing esoteric "magic", this should make dependencies type-safe, understandable, easier to test, and ultimately easier to deploy in production.

Defining Dependencies
Dependencies can be any python type. While in simple cases you might be able to pass a single object as a dependency (e.g. an HTTP connection), dataclasses are generally a convenient container when your dependencies included multiple objects.

Here's an example of defining an agent that requires dependencies.

(Note: dependencies aren't actually used in this example, see Accessing Dependencies below)


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayunused_dependencies.py

from dataclasses import dataclass

import httpx

from pydantic_ai import Agent


@dataclass
class MyDeps:  
    api_key: str
    http_client: httpx.AsyncClient


agent = Agent(
    'gateway/openai:gpt-5.2',
    deps_type=MyDeps,  
)


async def main():
    async with httpx.AsyncClient() as client:
        deps = MyDeps('foobar', client)
        result = await agent.run(
            'Tell me a joke.',
            deps=deps,  
        )
        print(result.output)
        #> Did you hear about the toothpaste scandal? They called it Colgate.

(This example is complete, it can be run "as is" — you'll need to add asyncio.run(main()) to run main)

Accessing Dependencies
Dependencies are accessed through the RunContext type, this should be the first parameter of system prompt functions etc.


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaysystem_prompt_dependencies.py

from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient


agent = Agent(
    'gateway/openai:gpt-5.2',
    deps_type=MyDeps,
)


@agent.system_prompt  
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:  
    response = await ctx.deps.http_client.get(  
        'https://example.com',
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},  
    )
    response.raise_for_status()
    return f'Prompt: {response.text}'


async def main():
    async with httpx.AsyncClient() as client:
        deps = MyDeps('foobar', client)
        result = await agent.run('Tell me a joke.', deps=deps)
        print(result.output)
        #> Did you hear about the toothpaste scandal? They called it Colgate.

(This example is complete, it can be run "as is" — you'll need to add asyncio.run(main()) to run main)

Asynchronous vs. Synchronous dependencies
System prompt functions, function tools and output validators are all run in the async context of an agent run.

If these functions are not coroutines (e.g. async def) they are called with run_in_executor in a thread pool. It's therefore marginally preferable to use async methods where dependencies perform IO, although synchronous dependencies should work fine too.

run vs. run_sync and Asynchronous vs. Synchronous dependencies

Whether you use synchronous or asynchronous dependencies is completely independent of whether you use run or run_sync — run_sync is just a wrapper around run and agents are always run in an async context.

Here's the same example as above, but with a synchronous dependency:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaysync_dependencies.py

from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.Client  


agent = Agent(
    'gateway/openai:gpt-5.2',
    deps_type=MyDeps,
)


@agent.system_prompt
def get_system_prompt(ctx: RunContext[MyDeps]) -> str:  
    response = ctx.deps.http_client.get(
        'https://example.com', headers={'Authorization': f'Bearer {ctx.deps.api_key}'}
    )
    response.raise_for_status()
    return f'Prompt: {response.text}'


async def main():
    deps = MyDeps('foobar', httpx.Client())
    result = await agent.run(
        'Tell me a joke.',
        deps=deps,
    )
    print(result.output)
    #> Did you hear about the toothpaste scandal? They called it Colgate.

(This example is complete, it can be run "as is" — you'll need to add asyncio.run(main()) to run main)

Full Example
As well as system prompts, dependencies can be used in tools and output validators.


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayfull_example.py

from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, ModelRetry, RunContext


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient


agent = Agent(
    'gateway/openai:gpt-5.2',
    deps_type=MyDeps,
)


@agent.system_prompt
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
    response = await ctx.deps.http_client.get('https://example.com')
    response.raise_for_status()
    return f'Prompt: {response.text}'


@agent.tool  
async def get_joke_material(ctx: RunContext[MyDeps], subject: str) -> str:
    response = await ctx.deps.http_client.get(
        'https://example.com#jokes',
        params={'subject': subject},
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
    )
    response.raise_for_status()
    return response.text


@agent.output_validator  
async def validate_output(ctx: RunContext[MyDeps], output: str) -> str:
    response = await ctx.deps.http_client.post(
        'https://example.com#validate',
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
        params={'query': output},
    )
    if response.status_code == 400:
        raise ModelRetry(f'invalid response: {response.text}')
    response.raise_for_status()
    return output


async def main():
    async with httpx.AsyncClient() as client:
        deps = MyDeps('foobar', client)
        result = await agent.run('Tell me a joke.', deps=deps)
        print(result.output)
        #> Did you hear about the toothpaste scandal? They called it Colgate.

(This example is complete, it can be run "as is" — you'll need to add asyncio.run(main()) to run main)

Overriding Dependencies
When testing agents, it's useful to be able to customise dependencies.

While this can sometimes be done by calling the agent directly within unit tests, we can also override dependencies while calling application code which in turn calls the agent.

This is done via the override method on the agent.


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayjoke_app.py

from dataclasses import dataclass

import httpx

from pydantic_ai import Agent, RunContext


@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient

    async def system_prompt_factory(self) -> str:  
        response = await self.http_client.get('https://example.com')
        response.raise_for_status()
        return f'Prompt: {response.text}'


joke_agent = Agent('gateway/openai:gpt-5.2', deps_type=MyDeps)


@joke_agent.system_prompt
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
    return await ctx.deps.system_prompt_factory()  


async def application_code(prompt: str) -> str:  
    ...
    ...
    # now deep within application code we call our agent
    async with httpx.AsyncClient() as client:
        app_deps = MyDeps('foobar', client)
        result = await joke_agent.run(prompt, deps=app_deps)  
    return result.output

(This example is complete, it can be run "as is")

test_joke_app.py

from joke_app import MyDeps, application_code, joke_agent


class TestMyDeps(MyDeps):  
    async def system_prompt_factory(self) -> str:
        return 'test prompt'


async def test_application_code():
    test_deps = TestMyDeps('test_key', None)  
    with joke_agent.override(deps=test_deps):  
        joke = await application_code('Tell me a joke.')  
    assert joke.startswith('Did you hear about the toothpaste scandal?')

Pydantic AI
Documentation
Tools & Toolsets
Function Tools
Function tools provide a mechanism for models to perform actions and retrieve extra information to help them generate a response.

They're useful when you want to enable the model to take some action and use the result, when it is impractical or impossible to put all the context an agent might need into the instructions, or when you want to make agents' behavior more deterministic or reliable by deferring some of the logic required to generate a response to another (not necessarily AI-powered) tool.

If you want a model to be able to call a function as its final action, without the result being sent back to the model, you can use an output function instead.

There are a number of ways to register tools with an agent:

via the @agent.tool decorator — for tools that need access to the agent context
via the @agent.tool_plain decorator — for tools that do not need access to the agent context
via the tools keyword argument to Agent which can take either plain functions, or instances of Tool
For more advanced use cases, the toolsets feature lets you manage collections of tools (built by you or provided by an MCP server or other third party) and register them with an agent in one go via the toolsets keyword argument to Agent. Internally, all tools and toolsets are gathered into a single combined toolset that's made available to the model.

Function tools vs. RAG

Function tools are basically the "R" of RAG (Retrieval-Augmented Generation) — they augment what the model can do by letting it request extra information.

The main semantic difference between Pydantic AI Tools and RAG is RAG is synonymous with vector search, while Pydantic AI tools are more general-purpose. For vector search, you can use our embeddings support to generate embeddings across multiple providers.

Function Tools vs. Structured Outputs

As the name suggests, function tools use the model's "tools" or "functions" API to let the model know what is available to call. Tools or functions are also used to define the schema(s) for structured output when using the default tool output mode, thus a model might have access to many tools, some of which call function tools while others end the run and produce a final output.

Registering via Decorator
@agent.tool is considered the default decorator since in the majority of cases tools will need access to the agent context.

Here's an example using both:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaydice_game.py

import random

from pydantic_ai import Agent, RunContext

agent = Agent(
    'gateway/gemini:gemini-3-flash-preview',  
    deps_type=str,  
    instructions=(
        "You're a dice game, you should roll the die and see if the number "
        "you get back matches the user's guess. If so, tell them they're a winner. "
        "Use the player's name in the response."
    ),
)


@agent.tool_plain  
def roll_dice() -> str:
    """Roll a six-sided die and return the result."""
    return str(random.randint(1, 6))


@agent.tool  
def get_player_name(ctx: RunContext[str]) -> str:
    """Get the player's name."""
    return ctx.deps


dice_result = agent.run_sync('My guess is 4', deps='Anne')  
print(dice_result.output)
#> Congratulations Anne, you guessed correctly! You're a winner!

(This example is complete, it can be run "as is")

Let's print the messages from that game to see what happened:

dice_game_messages.py

from dice_game import dice_result

print(dice_result.all_messages())
"""
[
    ModelRequest(
        parts=[
            UserPromptPart(
                content='My guess is 4',
                timestamp=datetime.datetime(...),
            )
        ],
        timestamp=datetime.datetime(...),
        instructions="You're a dice game, you should roll the die and see if the number you get back matches the user's guess. If so, tell them they're a winner. Use the player's name in the response.",
        run_id='...',
    ),
    ModelResponse(
        parts=[
            ToolCallPart(
                tool_name='roll_dice', args={}, tool_call_id='pyd_ai_tool_call_id'
            )
        ],
        usage=RequestUsage(input_tokens=54, output_tokens=2),
        model_name='gemini-3-flash-preview',
        timestamp=datetime.datetime(...),
        run_id='...',
    ),
    ModelRequest(
        parts=[
            ToolReturnPart(
                tool_name='roll_dice',
                content='4',
                tool_call_id='pyd_ai_tool_call_id',
                timestamp=datetime.datetime(...),
            )
        ],
        timestamp=datetime.datetime(...),
        instructions="You're a dice game, you should roll the die and see if the number you get back matches the user's guess. If so, tell them they're a winner. Use the player's name in the response.",
        run_id='...',
    ),
    ModelResponse(
        parts=[
            ToolCallPart(
                tool_name='get_player_name', args={}, tool_call_id='pyd_ai_tool_call_id'
            )
        ],
        usage=RequestUsage(input_tokens=55, output_tokens=4),
        model_name='gemini-3-flash-preview',
        timestamp=datetime.datetime(...),
        run_id='...',
    ),
    ModelRequest(
        parts=[
            ToolReturnPart(
                tool_name='get_player_name',
                content='Anne',
                tool_call_id='pyd_ai_tool_call_id',
                timestamp=datetime.datetime(...),
            )
        ],
        timestamp=datetime.datetime(...),
        instructions="You're a dice game, you should roll the die and see if the number you get back matches the user's guess. If so, tell them they're a winner. Use the player's name in the response.",
        run_id='...',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content="Congratulations Anne, you guessed correctly! You're a winner!"
            )
        ],
        usage=RequestUsage(input_tokens=56, output_tokens=12),
        model_name='gemini-3-flash-preview',
        timestamp=datetime.datetime(...),
        run_id='...',
    ),
]
"""
We can represent this with a diagram:

LLM
Agent
LLM
Agent
Send prompts
LLM decides to use
a tool
Rolls a six-sided die
LLM decides to use
another tool
Retrieves player name
LLM constructs final response
Game session complete
System: "You're a dice game..."
User: "My guess is 4"
Call tool
roll_dice()
ToolReturn
"4"
Call tool
get_player_name()
ToolReturn
"Anne"
ModelResponse
"Congratulations Anne, ..."
Registering via Agent Argument
As well as using the decorators, we can register tools via the tools argument to the Agent constructor. This is useful when you want to reuse tools, and can also give more fine-grained control over the tools.


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaydice_game_tool_kwarg.py

import random

from pydantic_ai import Agent, RunContext, Tool

instructions = """\
You're a dice game, you should roll the die and see if the number
you get back matches the user's guess. If so, tell them they're a winner.
Use the player's name in the response.
"""


def roll_dice() -> str:
    """Roll a six-sided die and return the result."""
    return str(random.randint(1, 6))


def get_player_name(ctx: RunContext[str]) -> str:
    """Get the player's name."""
    return ctx.deps


agent_a = Agent(
    'gateway/gemini:gemini-3-flash-preview',
    deps_type=str,
    tools=[roll_dice, get_player_name],  
    instructions=instructions,
)
agent_b = Agent(
    'gateway/gemini:gemini-3-flash-preview',
    deps_type=str,
    tools=[  
        Tool(roll_dice, takes_ctx=False),
        Tool(get_player_name, takes_ctx=True),
    ],
    instructions=instructions,
)

dice_result = {}
dice_result['a'] = agent_a.run_sync('My guess is 6', deps='Yashar')
dice_result['b'] = agent_b.run_sync('My guess is 4', deps='Anne')
print(dice_result['a'].output)
#> Tough luck, Yashar, you rolled a 4. Better luck next time.
print(dice_result['b'].output)
#> Congratulations Anne, you guessed correctly! You're a winner!

(This example is complete, it can be run "as is")

Tool Output
Tools can return anything that Pydantic can serialize to JSON. For advanced output options including multi-modal content and metadata, see Advanced Tool Features.

Tool Schema
Function parameters are extracted from the function signature, and all parameters except RunContext are used to build the schema for that tool call.

Even better, Pydantic AI extracts the docstring from functions and (thanks to griffe) extracts parameter descriptions from the docstring and adds them to the schema.

Griffe supports extracting parameter descriptions from google, numpy, and sphinx style docstrings. Pydantic AI will infer the format to use based on the docstring, but you can explicitly set it using docstring_format. You can also enforce parameter requirements by setting require_parameter_descriptions=True. This will raise a UserError if a parameter description is missing.

To demonstrate a tool's schema, here we use FunctionModel to print the schema a model would receive:

tool_schema.py

from pydantic_ai import Agent, ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

agent = Agent()


@agent.tool_plain(docstring_format='google', require_parameter_descriptions=True)
def foobar(a: int, b: str, c: dict[str, list[float]]) -> str:
    """Get me foobar.

    Args:
        a: apple pie
        b: banana cake
        c: carrot smoothie
    """
    return f'{a} {b} {c}'


def print_schema(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    tool = info.function_tools[0]
    print(tool.description)
    #> Get me foobar.
    print(tool.parameters_json_schema)
    """
    {
        'additionalProperties': False,
        'properties': {
            'a': {'description': 'apple pie', 'type': 'integer'},
            'b': {'description': 'banana cake', 'type': 'string'},
            'c': {
                'additionalProperties': {'items': {'type': 'number'}, 'type': 'array'},
                'description': 'carrot smoothie',
                'type': 'object',
            },
        },
        'required': ['a', 'b', 'c'],
        'type': 'object',
    }
    """
    return ModelResponse(parts=[TextPart('foobar')])


agent.run_sync('hello', model=FunctionModel(print_schema))
(This example is complete, it can be run "as is")

If a tool has a single parameter that can be represented as an object in JSON schema (e.g. dataclass, TypedDict, pydantic model), the schema for the tool is simplified to be just that object.

Here's an example where we use TestModel.last_model_request_parameters to inspect the tool schema that would be passed to the model.

single_parameter_tool.py

from pydantic import BaseModel

from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

agent = Agent()


class Foobar(BaseModel):
    """This is a Foobar"""

    x: int
    y: str
    z: float = 3.14


@agent.tool_plain
def foobar(f: Foobar) -> str:
    return str(f)


test_model = TestModel()
result = agent.run_sync('hello', model=test_model)
print(result.output)
#> {"foobar":"x=0 y='a' z=3.14"}
print(test_model.last_model_request_parameters.function_tools)
"""
[
    ToolDefinition(
        name='foobar',
        parameters_json_schema={
            'properties': {
                'x': {'type': 'integer'},
                'y': {'type': 'string'},
                'z': {'default': 3.14, 'type': 'number'},
            },
            'required': ['x', 'y'],
            'title': 'Foobar',
            'type': 'object',
        },
        description='This is a Foobar',
    )
]
"""
(This example is complete, it can be run "as is")

Debugging Tool Calls

Understanding tool behavior is crucial for agent development. By instrumenting your agent with Logfire, you can see:

What arguments were passed to each tool
What each tool returned
How long each tool took to execute
Any errors that occurred
This visibility helps you understand why an agent made specific decisions and identify issues in tool implementations.

Output
"Output" refers to the final value returned from running an agent. This can be either plain text, structured data, an image, or the result of a function called with arguments provided by the model.

The output is wrapped in AgentRunResult or StreamedRunResult so that you can access other data, like usage of the run and message history.

Both AgentRunResult and StreamedRunResult are generic in the data they wrap, so typing information about the data returned by the agent is preserved.

A run ends when the model responds with one of the output types, or, if no output type is specified or str is one of the allowed options, when a plain text response is received. A run can also be cancelled if usage limits are exceeded, see Usage Limits.

Here's an example using a Pydantic model as the output_type, forcing the model to respond with data matching our specification:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayolympics.py

from pydantic import BaseModel

from pydantic_ai import Agent


class CityLocation(BaseModel):
    city: str
    country: str


agent = Agent('gateway/gemini:gemini-3-flash-preview', output_type=CityLocation)
result = agent.run_sync('Where were the olympics held in 2012?')
print(result.output)
#> city='London' country='United Kingdom'
print(result.usage())
#> RunUsage(input_tokens=57, output_tokens=8, requests=1)

(This example is complete, it can be run "as is")

Structured output data
The Agent class constructor takes an output_type argument that takes one or more types or output functions. It supports simple scalar types, list and dict types (including TypedDicts and StructuredDicts), dataclasses and Pydantic models, as well as type unions -- generally everything supported as type hints in a Pydantic model. You can also pass a list of multiple choices.

By default, Pydantic AI leverages the model's tool calling capability to make it return structured data. When multiple output types are specified (in a union or list), each member is registered with the model as a separate output tool in order to reduce the complexity of the schema and maximise the chances a model will respond correctly. This has been shown to work well across a wide range of models. If you'd like to change the names of the output tools, use a model's native structured output feature, or pass the output schema to the model in its instructions, you can use an output mode marker class.

When no output type is specified, or when str is among the output types, any plain text response from the model will be used as the output data. If str is not among the output types, the model is forced to return structured data or call an output function.

If the output type schema is not of type "object" (e.g. it's int or list[int]), the output type is wrapped in a single element object, so the schema of all tools registered with the model are object schemas.

Structured outputs (like tools) use Pydantic to build the JSON schema used for the tool, and to validate the data returned by the model.

Type checking considerations

The Agent class is generic in its output type, and this type is carried through to AgentRunResult.output and StreamedRunResult.output so that your IDE or static type checker can warn you when your code doesn't properly take into account all the possible values those outputs could have.

Static type checkers like pyright and mypy will do their best to infer the agent's output type from the output_type you've specified, but they're not always able to do so correctly when you provide functions or multiple types in a union or list, even though Pydantic AI will behave correctly. When this happens, your type checker will complain even when you're confident you've passed a valid output_type, and you'll need to help the type checker by explicitly specifying the generic parameters on the Agent constructor. This is shown in the second example below and the output functions example further down.

Specifically, there are three valid uses of output_type where you'll need to do this:

When using a union of types, e.g. output_type=Foo | Bar. Until PEP-747 "Annotating Type Forms" lands in Python 3.15, type checkers do not consider these a valid value for output_type. In addition to the generic parameters on the Agent constructor, you'll need to add # type: ignore to the line that passes the union to output_type. Alternatively, you can use a list: output_type=[Foo, Bar].
With mypy: When using a list, as a functionally equivalent alternative to a union, or because you're passing in output functions. Pyright does handle this correctly, and we've filed an issue with mypy to try and get this fixed.
With mypy: when using an async output function. Pyright does handle this correctly, and we've filed an issue with mypy to try and get this fixed.
Here's an example of returning either text or structured data:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaybox_or_error.py

from pydantic import BaseModel

from pydantic_ai import Agent


class Box(BaseModel):
    width: int
    height: int
    depth: int
    units: str


agent = Agent(
    'gateway/openai:gpt-5-mini',
    output_type=[Box, str], 
    instructions=(
        "Extract me the dimensions of a box, "
        "if you can't extract all data, ask the user to try again."
    ),
)

result = agent.run_sync('The box is 10x20x30')
print(result.output)
#> Please provide the units for the dimensions (e.g., cm, in, m).

result = agent.run_sync('The box is 10x20x30 cm')
print(result.output)
#> width=10 height=20 depth=30 units='cm'

(This example is complete, it can be run "as is")

Here's an example of using a union return type, which will register multiple output tools and wrap non-object schemas in an object:

colors_or_sizes.py

from pydantic_ai import Agent

agent = Agent[None, list[str] | list[int]](
    'openai:gpt-5-mini',
    output_type=list[str] | list[int],  
    instructions='Extract either colors or sizes from the shapes provided.',
)

result = agent.run_sync('red square, blue circle, green triangle')
print(result.output)
#> ['red', 'blue', 'green']

result = agent.run_sync('square size 10, circle size 20, triangle size 30')
print(result.output)
#> [10, 20, 30]
(This example is complete, it can be run "as is")

Output functions
Instead of plain text or structured data, you may want the output of your agent run to be the result of a function called with arguments provided by the model, for example to further process or validate the data provided through the arguments (with the option to tell the model to try again), or to hand off to another agent.

Output functions are similar to function tools, but the model is forced to call one of them, the call ends the agent run, and the result is not passed back to the model.

As with tool functions, output function arguments provided by the model are validated using Pydantic (with optional validation context), can optionally take RunContext as the first argument, and can raise ModelRetry to ask the model to try again with modified arguments (or with a different output type).

To specify output functions, you set the agent's output_type to either a single function (or bound instance method), or a list of functions. The list can also contain other output types like simple scalars or entire Pydantic models. You typically do not want to also register your output function as a tool (using the @agent.tool decorator or tools argument), as this could confuse the model about which it should be calling.

Here's an example of all of these features in action:

output_functions.py

import re

from pydantic import BaseModel

from pydantic_ai import Agent, ModelRetry, RunContext, UnexpectedModelBehavior


class Row(BaseModel):
    name: str
    country: str


tables = {
    'capital_cities': [
        Row(name='Amsterdam', country='Netherlands'),
        Row(name='Mexico City', country='Mexico'),
    ]
}


class SQLFailure(BaseModel):
    """An unrecoverable failure. Only use this when you can't change the query to make it work."""

    explanation: str


def run_sql_query(query: str) -> list[Row]:
    """Run a SQL query on the database."""

    select_table = re.match(r'SELECT (.+) FROM (\w+)', query)
    if select_table:
        column_names = select_table.group(1)
        if column_names != '*':
            raise ModelRetry("Only 'SELECT *' is supported, you'll have to do column filtering manually.")

        table_name = select_table.group(2)
        if table_name not in tables:
            raise ModelRetry(
                f"Unknown table '{table_name}' in query '{query}'. Available tables: {', '.join(tables.keys())}."
            )

        return tables[table_name]

    raise ModelRetry(f"Unsupported query: '{query}'.")


sql_agent = Agent[None, list[Row] | SQLFailure](
    'openai:gpt-5.2',
    output_type=[run_sql_query, SQLFailure],
    instructions='You are a SQL agent that can run SQL queries on a database.',
)


async def hand_off_to_sql_agent(ctx: RunContext, query: str) -> list[Row]:
    """I take natural language queries, turn them into SQL, and run them on a database."""

    # Drop the final message with the output tool call, as it shouldn't be passed on to the SQL agent
    messages = ctx.messages[:-1]
    try:
        result = await sql_agent.run(query, message_history=messages)
        output = result.output
        if isinstance(output, SQLFailure):
            raise ModelRetry(f'SQL agent failed: {output.explanation}')
        return output
    except UnexpectedModelBehavior as e:
        # Bubble up potentially retryable errors to the router agent
        if (cause := e.__cause__) and isinstance(cause, ModelRetry):
            raise ModelRetry(f'SQL agent failed: {cause.message}') from e
        else:
            raise


class RouterFailure(BaseModel):
    """Use me when no appropriate agent is found or the used agent failed."""

    explanation: str


router_agent = Agent[None, list[Row] | RouterFailure](
    'openai:gpt-5.2',
    output_type=[hand_off_to_sql_agent, RouterFailure],
    instructions='You are a router to other agents. Never try to solve a problem yourself, just pass it on.',
)

result = router_agent.run_sync('Select the names and countries of all capitals')
print(result.output)
"""
[
    Row(name='Amsterdam', country='Netherlands'),
    Row(name='Mexico City', country='Mexico'),
]
"""

result = router_agent.run_sync('Select all pets')
print(repr(result.output))
"""
RouterFailure(explanation="The requested table 'pets' does not exist in the database. The only available table is 'capital_cities', which does not contain data about pets.")
"""

result = router_agent.run_sync('How do I fly from Amsterdam to Mexico City?')
print(repr(result.output))
"""
RouterFailure(explanation='I am not equipped to provide travel information, such as flights from Amsterdam to Mexico City.')
"""
Text output
If you provide an output function that takes a string, Pydantic AI will by default create an output tool like for any other output function. If instead you'd like the model to provide the string using plain text output, you can wrap the function in the TextOutput marker class.

If desired, this marker class can be used alongside one or more ToolOutput marker classes (or unmarked types or functions) in a list provided to output_type.

Like other output functions, text output functions can optionally take RunContext as the first argument, and can raise ModelRetry to ask the model to try again with modified arguments (or with a different output type).


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaytext_output_function.py

from pydantic_ai import Agent, TextOutput


def split_into_words(text: str) -> list[str]:
    return text.split()


agent = Agent(
    'gateway/openai:gpt-5.2',
    output_type=TextOutput(split_into_words),
)
result = agent.run_sync('Who was Albert Einstein?')
print(result.output)
#> ['Albert', 'Einstein', 'was', 'a', 'German-born', 'theoretical', 'physicist.']

(This example is complete, it can be run "as is")

Handling partial output in output functions
When streaming with run_stream() or run_stream_sync(), output functions are called multiple times — once for each partial output received from the model, and once for the final complete output.

You should check the RunContext.partial_output flag when your output function has side effects (e.g., sending notifications, logging, database updates) that should only execute on the final output.

When streaming, partial_output is True for each partial output and False for the final complete output. For all other run methods, partial_output is always False as the function is only called once with the complete output.


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayoutput_function_with_side_effects.py

from pydantic import BaseModel

from pydantic_ai import Agent, RunContext


class DatabaseRecord(BaseModel):
    name: str
    value: int | None = None  # Make optional to allow partial output


def save_to_database(ctx: RunContext, record: DatabaseRecord) -> DatabaseRecord:
    """Output function with side effect - only save final output to database."""
    if ctx.partial_output:
        # Skip side effects for partial outputs
        return record

    # Only execute side effect for the final output
    print(f'Saving to database: {record.name} = {record.value}')
    #> Saving to database: test = 42
    return record


agent = Agent('gateway/openai:gpt-5.2', output_type=save_to_database)


async def main():
    async with agent.run_stream('Create a record with name "test" and value 42') as result:
        async for output in result.stream_output(debounce_by=None):
            print(output)
            #> name='test' value=None
            #> name='test' value=42

(This example is complete, it can be run "as is" — you'll need to add asyncio.run(main()) to run main)

Output modes
Pydantic AI implements three different methods to get a model to output structured data:

Tool Output, where tool calls are used to produce the output.
Native Output, where the model is required to produce text content compliant with a provided JSON schema.
Prompted Output, where a prompt is injected into the model instructions including the desired JSON schema, and we attempt to parse the model's plain-text response as appropriate.
Tool Output
In the default Tool Output mode, the output JSON schema of each output type (or function) is provided to the model as the parameters schema of a special output tool. This is the default as it's supported by virtually all models and has been shown to work very well.

If you'd like to change the name of the output tool, pass a custom description to aid the model, or turn on or off strict mode, you can wrap the type(s) in the ToolOutput marker class and provide the appropriate arguments. Note that by default, the description is taken from the docstring specified on a Pydantic model or output function, so specifying it using the marker class is typically not necessary.

To dynamically modify or filter the available output tools during an agent run, you can define an agent-wide prepare_output_tools function that will be called ahead of each step of a run. This function should be of type ToolsPrepareFunc, which takes the RunContext and a list of ToolDefinition, and returns a new list of tool definitions (or None to disable all tools for that step). This is analogous to the prepare_tools function for non-output tools.


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaytool_output.py

from pydantic import BaseModel

from pydantic_ai import Agent, ToolOutput


class Fruit(BaseModel):
    name: str
    color: str


class Vehicle(BaseModel):
    name: str
    wheels: int


agent = Agent(
    'gateway/openai:gpt-5.2',
    output_type=[ 
        ToolOutput(Fruit, name='return_fruit'),
        ToolOutput(Vehicle, name='return_vehicle'),
    ],
)
result = agent.run_sync('What is a banana?')
print(repr(result.output))
#> Fruit(name='banana', color='yellow')

(This example is complete, it can be run "as is")

Parallel Output Tool Calls
When the model calls other tools in parallel with an output tool, you can control how tool calls are executed by setting the agent's end_strategy:

'early' (default): Output tools are executed first. Once a valid final result is found, remaining function and output tool calls are skipped
'exhaustive': Output tools are executed first, then all function tools are executed. The first valid output tool result becomes the final output
The 'exhaustive' strategy is useful when tools have important side effects (like logging, sending notifications, or updating metrics) that should always execute.

Priority of output and deferred tools in streaming methods

The run_stream() and run_stream_sync() methods will consider the first output that matches the output type (which could be text, an output tool call, or a deferred tool call) to be the final output of the agent run, even when the model generates (additional) tool calls after this "final" output.

This means that if the model calls deferred tools before output tools when using these methods, the deferred tool calls determine the agent run's final output, while the other run methods would have prioritized the tool output.

Native Output
Native Output mode uses a model's native "Structured Outputs" feature (aka "JSON Schema response format"), where the model is forced to only output text matching the provided JSON schema. Note that this is not supported by all models, and sometimes comes with restrictions. For example, Gemini cannot use tools at the same time as structured output, and attempting to do so will result in an error.

To use this mode, you can wrap the output type(s) in the NativeOutput marker class that also lets you specify a name and description if the name and docstring of the type or function are not sufficient.


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaynative_output.py

from pydantic_ai import Agent, NativeOutput

from tool_output import Fruit, Vehicle

agent = Agent(
    'gateway/openai:gpt-5.2',
    output_type=NativeOutput(
        [Fruit, Vehicle], 
        name='Fruit_or_vehicle',
        description='Return a fruit or vehicle.'
    ),
)
result = agent.run_sync('What is a Ford Explorer?')
print(repr(result.output))
#> Vehicle(name='Ford Explorer', wheels=4)

(This example is complete, it can be run "as is")

Prompted Output
In this mode, the model is prompted to output text matching the provided JSON schema through its instructions and it's up to the model to interpret those instructions correctly. This is usable with all models, but is often the least reliable approach as the model is not forced to match the schema.

While we would generally suggest starting with tool or native output, in some cases this mode may result in higher quality outputs, and for models without native tool calling or structured output support it is the only option for producing structured outputs.

If the model API supports the "JSON Mode" feature (aka "JSON Object response format") to force the model to output valid JSON, this is enabled, but it's still up to the model to abide by the schema. Pydantic AI will validate the returned structured data and tell the model to try again if validation fails, but if the model is not intelligent enough this may not be sufficient.

To use this mode, you can wrap the output type(s) in the PromptedOutput marker class that also lets you specify a name and description if the name and docstring of the type or function are not sufficient. Additionally, it supports an template argument lets you specify a custom instructions template to be used instead of the default.


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayprompted_output.py

from pydantic import BaseModel

from pydantic_ai import Agent, PromptedOutput

from tool_output import Vehicle


class Device(BaseModel):
    name: str
    kind: str


agent = Agent(
    'gateway/openai:gpt-5.2',
    output_type=PromptedOutput(
        [Vehicle, Device], 
        name='Vehicle or device',
        description='Return a vehicle or device.'
    ),
)
result = agent.run_sync('What is a MacBook?')
print(repr(result.output))
#> Device(name='MacBook', kind='laptop')

agent = Agent(
    'gateway/openai:gpt-5.2',
    output_type=PromptedOutput(
        [Vehicle, Device],
        template='Gimme some JSON: {schema}'
    ),
)
result = agent.run_sync('What is a Ford Explorer?')
print(repr(result.output))
#> Vehicle(name='Ford Explorer', wheels=4)

(This example is complete, it can be run "as is")

Custom JSON schema
If it's not feasible to define your desired structured output object using a Pydantic BaseModel, dataclass, or TypedDict, for example when you get a JSON schema from an external source or generate it dynamically, you can use the StructuredDict() helper function to generate a dict[str, Any] subclass with a JSON schema attached that Pydantic AI will pass to the model.

Note that Pydantic AI will not perform any validation of the received JSON object and it's up to the model to correctly interpret the schema and any constraints expressed in it, like required fields or integer value ranges.

The output type will be a dict[str, Any] and it's up to your code to defensively read from it in case the model made a mistake. You can use an output validator to reflect validation errors back to the model and get it to try again.

Along with the JSON schema, you can optionally pass name and description arguments to provide additional context to the model:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gateway

from pydantic_ai import Agent, StructuredDict

HumanDict = StructuredDict(
    {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'age': {'type': 'integer'}
        },
        'required': ['name', 'age']
    },
    name='Human',
    description='A human with a name and age',
)

agent = Agent('gateway/openai:gpt-5.2', output_type=HumanDict)
result = agent.run_sync('Create a person')
#> {'name': 'John Doe', 'age': 30}

Validation context
Some validation relies on an extra Pydantic context object. You can pass such an object to an Agent at definition-time via its validation_context parameter. It will be used in the validation of both structured outputs and tool arguments.

This validation context can be either:

the context object itself (Any), used as-is to validate outputs, or
a function that takes the RunContext and returns a context object (Any). This function will be called automatically before each validation, allowing you to build a dynamic validation context.
Don't confuse this validation context with the LLM context

This Pydantic validation context object is only used internally by Pydantic AI for tool arg and output validation. In particular, it is not included in the prompts or messages sent to the language model.


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayvalidation_context.py

from dataclasses import dataclass

from pydantic import BaseModel, ValidationInfo, field_validator

from pydantic_ai import Agent


class Value(BaseModel):
    x: int

    @field_validator('x')
    def increment_value(cls, value: int, info: ValidationInfo):
        return value + (info.context or 0)


agent = Agent(
    'gateway/gemini:gemini-3-flash-preview',
    output_type=Value,
    validation_context=10,
)
result = agent.run_sync('Give me a value of 5.')
print(repr(result.output))  # 5 from the model + 10 from the validation context
#> Value(x=15)


@dataclass
class Deps:
    increment: int


agent = Agent(
    'gateway/gemini:gemini-3-flash-preview',
    output_type=Value,
    deps_type=Deps,
    validation_context=lambda ctx: ctx.deps.increment,
)
result = agent.run_sync('Give me a value of 5.', deps=Deps(increment=10))
print(repr(result.output))  # 5 from the model + 10 from the validation context
#> Value(x=15)

(This example is complete, it can be run "as is")

Output validators
Some validation is inconvenient or impossible to do in Pydantic validators, in particular when the validation requires IO and is asynchronous. Pydantic AI provides a way to add validation functions via the agent.output_validator decorator.

If you want to implement separate validation logic for different output types, it's recommended to use output functions instead, to save you from having to do isinstance checks inside the output validator. If you want the model to output plain text, do your own processing or validation, and then have the agent's final output be the result of your function, it's recommended to use an output function with the TextOutput marker class.

Here's a simplified variant of the SQL Generation example:

sql_gen.py

from fake_database import DatabaseConn, QueryError
from pydantic import BaseModel

from pydantic_ai import Agent, RunContext, ModelRetry


class Success(BaseModel):
    sql_query: str


class InvalidRequest(BaseModel):
    error_message: str


Output = Success | InvalidRequest
agent = Agent[DatabaseConn, Output](
    'google-gla:gemini-3-flash-preview',
    output_type=Output,  # type: ignore
    deps_type=DatabaseConn,
    instructions='Generate PostgreSQL flavored SQL queries based on user input.',
)


@agent.output_validator
async def validate_sql(ctx: RunContext[DatabaseConn], output: Output) -> Output:
    if isinstance(output, InvalidRequest):
        return output
    try:
        await ctx.deps.execute(f'EXPLAIN {output.sql_query}')
    except QueryError as e:
        raise ModelRetry(f'Invalid query: {e}') from e
    else:
        return output


result = agent.run_sync(
    'get me users who were last active yesterday.', deps=DatabaseConn()
)
print(result.output)
#> sql_query='SELECT * FROM users WHERE last_active::date = today() - interval 1 day'
(This example is complete, it can be run "as is")

Handling partial output in output validators
When streaming with run_stream() or run_stream_sync(), output validators are called multiple times — once for each partial output received from the model, and once for the final complete output.

You should check the RunContext.partial_output flag when you want to validate only the complete result, not intermediate partial values.

When streaming, partial_output is True for each partial output and False for the final complete output. For all other run methods, partial_output is always False as the validator is only called once with the complete output.


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaypartial_validation_streaming.py

from pydantic_ai import Agent, ModelRetry, RunContext

agent = Agent('gateway/openai:gpt-5.2')


@agent.output_validator
def validate_output(ctx: RunContext, output: str) -> str:
    if ctx.partial_output:
        return output

    if len(output) < 50:
        raise ModelRetry('Output is too short.')
    return output


async def main():
    async with agent.run_stream('Write a long story about a cat') as result:
        async for message in result.stream_text():
            print(message)
            #> Once upon a
            #> Once upon a time, there was
            #> Once upon a time, there was a curious cat
            #> Once upon a time, there was a curious cat named Whiskers who
            #> Once upon a time, there was a curious cat named Whiskers who loved to explore
            #> Once upon a time, there was a curious cat named Whiskers who loved to explore the world around
            #> Once upon a time, there was a curious cat named Whiskers who loved to explore the world around him...

(This example is complete, it can be run "as is" — you'll need to add asyncio.run(main()) to run main)

Image output
Some models can generate images as part of their response, for example those that support the Image Generation built-in tool and OpenAI models using the Code Execution built-in tool when told to generate a chart.

To use the generated image as the output of the agent run, you can set output_type to BinaryImage. If no image-generating built-in tool is explicitly specified, the ImageGenerationTool will be enabled automatically.


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayimage_output.py

from pydantic_ai import Agent, BinaryImage

agent = Agent('gateway/openai-responses:gpt-5.2', output_type=BinaryImage)

result = agent.run_sync('Generate an image of an axolotl.')
assert isinstance(result.output, BinaryImage)

(This example is complete, it can be run "as is")

If an agent does not need to always generate an image, you can use a union of BinaryImage and str. If the model generates both, the image will take precedence as output and the text will be available on ModelResponse.text:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayimage_output_union.py

from pydantic_ai import Agent, BinaryImage

agent = Agent('gateway/openai-responses:gpt-5.2', output_type=BinaryImage | str)

result = agent.run_sync('Tell me a two-sentence story about an axolotl, no image please.')
print(result.output)
"""
Once upon a time, in a hidden underwater cave, lived a curious axolotl named Pip who loved to explore. One day, while venturing further than usual, Pip discovered a shimmering, ancient coin that granted wishes!
"""

result = agent.run_sync('Tell me a two-sentence story about an axolotl with an illustration.')
assert isinstance(result.output, BinaryImage)
print(result.response.text)
"""
Once upon a time, in a hidden underwater cave, lived a curious axolotl named Pip who loved to explore. One day, while venturing further than usual, Pip discovered a shimmering, ancient coin that granted wishes!
"""

Streamed Results
There two main challenges with streamed results:

Validating structured responses before they're complete, this is achieved by "partial validation" which was recently added to Pydantic in pydantic/pydantic#10748.
When receiving a response, we don't know if it's the final response without starting to stream it and peeking at the content. Pydantic AI streams just enough of the response to sniff out if it's a tool call or an output, then streams the whole thing and calls tools, or returns the stream as a StreamedRunResult.
Note

As the run_stream() method will consider the first output matching the output_type to be the final output, it will stop running the agent graph and will not execute any tool calls made by the model after this "final" output.

If you want to always run the agent graph to completion and stream all events from the model's streaming response and the agent's execution of tools, use agent.run_stream_events() (docs) or agent.iter() (docs) instead.

Streaming Text
Example of streamed text output:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaystreamed_hello_world.py

from pydantic_ai import Agent

agent = Agent('gateway/gemini:gemini-3-flash-preview')  


async def main():
    async with agent.run_stream('Where does "hello world" come from?') as result:  
        async for message in result.stream_text():  
            print(message)
            #> The first known
            #> The first known use of "hello,
            #> The first known use of "hello, world" was in
            #> The first known use of "hello, world" was in a 1974 textbook
            #> The first known use of "hello, world" was in a 1974 textbook about the C
            #> The first known use of "hello, world" was in a 1974 textbook about the C programming language.

(This example is complete, it can be run "as is" — you'll need to add asyncio.run(main()) to run main)

We can also stream text as deltas rather than the entire text in each item:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaystreamed_delta_hello_world.py

from pydantic_ai import Agent

agent = Agent('gateway/gemini:gemini-3-flash-preview')


async def main():
    async with agent.run_stream('Where does "hello world" come from?') as result:
        async for message in result.stream_text(delta=True):  
            print(message)
            #> The first known
            #> use of "hello,
            #> world" was in
            #> a 1974 textbook
            #> about the C
            #> programming language.

(This example is complete, it can be run "as is" — you'll need to add asyncio.run(main()) to run main)

Output message not included in messages

The final output message will NOT be added to result messages if you use .stream_text(delta=True), see Messages and chat history for more information.

Streaming Structured Output
Here's an example of streaming a user profile as it's built:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaystreamed_user_profile.py

from datetime import date

from typing_extensions import NotRequired, TypedDict

from pydantic_ai import Agent


class UserProfile(TypedDict):
    name: str
    dob: NotRequired[date]
    bio: NotRequired[str]


agent = Agent(
    'gateway/openai:gpt-5.2',
    output_type=UserProfile,
    instructions='Extract a user profile from the input',
)


async def main():
    user_input = 'My name is Ben, I was born on January 28th 1990, I like the chain the dog and the pyramid.'
    async with agent.run_stream(user_input) as result:
        async for profile in result.stream_output():
            print(profile)
            #> {'name': 'Ben'}
            #> {'name': 'Ben'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the '}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyr'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}

(This example is complete, it can be run "as is" — you'll need to add asyncio.run(main()) to run main)

As setting an output_type uses the Tool Output mode by default, this will only work if the model supports streaming tool arguments. For models that don't, like Gemini, try Native Output or Prompted Output instead.

Streaming Model Responses
If you want fine-grained control of validation, you can use the following pattern to get the entire partial ModelResponse:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaystreamed_user_profile.py

from datetime import date

from pydantic import ValidationError
from typing_extensions import TypedDict

from pydantic_ai import Agent


class UserProfile(TypedDict, total=False):
    name: str
    dob: date
    bio: str


agent = Agent('gateway/openai:gpt-5.2', output_type=UserProfile)


async def main():
    user_input = 'My name is Ben, I was born on January 28th 1990, I like the chain the dog and the pyramid.'
    async with agent.run_stream(user_input) as result:
        async for message, last in result.stream_responses(debounce_by=0.01):  
            try:
                profile = await result.validate_response_output(  
                    message,
                    allow_partial=not last,
                )
            except ValidationError:
                continue
            print(profile)
            #> {'name': 'Ben'}
            #> {'name': 'Ben'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the '}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyr'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}

(This example is complete, it can be run "as is" — you'll need to add asyncio.run(main()) to run main)

Pydantic AI
Documentation
Core Concepts
Messages and chat history
Pydantic AI provides access to messages exchanged during an agent run. These messages can be used both to continue a coherent conversation, and to understand how an agent performed.

Accessing Messages from Results
After running an agent, you can access the messages exchanged during that run from the result object.

Both RunResult (returned by Agent.run, Agent.run_sync) and StreamedRunResult (returned by Agent.run_stream) have the following methods:

all_messages(): returns all messages, including messages from prior runs. There's also a variant that returns JSON bytes, all_messages_json().
new_messages(): returns only the messages from the current run. There's also a variant that returns JSON bytes, new_messages_json().
StreamedRunResult and complete messages

On StreamedRunResult, the messages returned from these methods will only include the final result message once the stream has finished.

E.g. you've awaited one of the following coroutines:

StreamedRunResult.stream_output()
StreamedRunResult.stream_text()
StreamedRunResult.stream_responses()
StreamedRunResult.get_output()
Note: The final result message will NOT be added to result messages if you use .stream_text(delta=True) since in this case the result content is never built as one string.

Example of accessing methods on a RunResult :


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayrun_result_messages.py

from pydantic_ai import Agent

agent = Agent('gateway/openai:gpt-5.2', instructions='Be a helpful assistant.')

result = agent.run_sync('Tell me a joke.')
print(result.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.

# all messages from the run
print(result.all_messages())
"""
[
    ModelRequest(
        parts=[
            UserPromptPart(
                content='Tell me a joke.',
                timestamp=datetime.datetime(...),
            )
        ],
        timestamp=datetime.datetime(...),
        instructions='Be a helpful assistant.',
        run_id='...',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='Did you hear about the toothpaste scandal? They called it Colgate.'
            )
        ],
        usage=RequestUsage(input_tokens=55, output_tokens=12),
        model_name='gpt-5.2',
        timestamp=datetime.datetime(...),
        run_id='...',
    ),
]
"""

(This example is complete, it can be run "as is")

Example of accessing methods on a StreamedRunResult :


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaystreamed_run_result_messages.py

from pydantic_ai import Agent

agent = Agent('gateway/openai:gpt-5.2', instructions='Be a helpful assistant.')


async def main():
    async with agent.run_stream('Tell me a joke.') as result:
        # incomplete messages before the stream finishes
        print(result.all_messages())
        """
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='Tell me a joke.',
                        timestamp=datetime.datetime(...),
                    )
                ],
                timestamp=datetime.datetime(...),
                instructions='Be a helpful assistant.',
                run_id='...',
            )
        ]
        """

        async for text in result.stream_text():
            print(text)
            #> Did you hear
            #> Did you hear about the toothpaste
            #> Did you hear about the toothpaste scandal? They called
            #> Did you hear about the toothpaste scandal? They called it Colgate.

        # complete messages once the stream finishes
        print(result.all_messages())
        """
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='Tell me a joke.',
                        timestamp=datetime.datetime(...),
                    )
                ],
                timestamp=datetime.datetime(...),
                instructions='Be a helpful assistant.',
                run_id='...',
            ),
            ModelResponse(
                parts=[
                    TextPart(
                        content='Did you hear about the toothpaste scandal? They called it Colgate.'
                    )
                ],
                usage=RequestUsage(input_tokens=50, output_tokens=12),
                model_name='gpt-5.2',
                timestamp=datetime.datetime(...),
                run_id='...',
            ),
        ]
        """

(This example is complete, it can be run "as is" — you'll need to add asyncio.run(main()) to run main)

Using Messages as Input for Further Agent Runs
The primary use of message histories in Pydantic AI is to maintain context across multiple agent runs.

To use existing messages in a run, pass them to the message_history parameter of Agent.run, Agent.run_sync or Agent.run_stream.

If message_history is set and not empty, a new system prompt is not generated — we assume the existing message history includes a system prompt.


With Pydantic AI Gateway
Directly to Provider API
Learn about GatewayReusing messages in a conversation

from pydantic_ai import Agent

agent = Agent('gateway/openai:gpt-5.2', instructions='Be a helpful assistant.')

result1 = agent.run_sync('Tell me a joke.')
print(result1.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.

result2 = agent.run_sync('Explain?', message_history=result1.new_messages())
print(result2.output)
#> This is an excellent joke invented by Samuel Colvin, it needs no explanation.

print(result2.all_messages())
"""
[
    ModelRequest(
        parts=[
            UserPromptPart(
                content='Tell me a joke.',
                timestamp=datetime.datetime(...),
            )
        ],
        timestamp=datetime.datetime(...),
        instructions='Be a helpful assistant.',
        run_id='...',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='Did you hear about the toothpaste scandal? They called it Colgate.'
            )
        ],
        usage=RequestUsage(input_tokens=55, output_tokens=12),
        model_name='gpt-5.2',
        timestamp=datetime.datetime(...),
        run_id='...',
    ),
    ModelRequest(
        parts=[
            UserPromptPart(
                content='Explain?',
                timestamp=datetime.datetime(...),
            )
        ],
        timestamp=datetime.datetime(...),
        instructions='Be a helpful assistant.',
        run_id='...',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='This is an excellent joke invented by Samuel Colvin, it needs no explanation.'
            )
        ],
        usage=RequestUsage(input_tokens=56, output_tokens=26),
        model_name='gpt-5.2',
        timestamp=datetime.datetime(...),
        run_id='...',
    ),
]
"""

(This example is complete, it can be run "as is")

Storing and loading messages (to JSON)
While maintaining conversation state in memory is enough for many applications, often times you may want to store the messages history of an agent run on disk or in a database. This might be for evals, for sharing data between Python and JavaScript/TypeScript, or any number of other use cases.

The intended way to do this is using a TypeAdapter.

We export ModelMessagesTypeAdapter that can be used for this, or you can create your own.

Here's an example showing how:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewayserialize messages to json

from pydantic_core import to_jsonable_python

from pydantic_ai import (
    Agent,
    ModelMessagesTypeAdapter,  
)

agent = Agent('gateway/openai:gpt-5.2', instructions='Be a helpful assistant.')

result1 = agent.run_sync('Tell me a joke.')
history_step_1 = result1.all_messages()
as_python_objects = to_jsonable_python(history_step_1)  
same_history_as_step_1 = ModelMessagesTypeAdapter.validate_python(as_python_objects)

result2 = agent.run_sync(  
    'Tell me a different joke.', message_history=same_history_as_step_1
)

(This example is complete, it can be run "as is")

Other ways of using messages
Since messages are defined by simple dataclasses, you can manually create and manipulate, e.g. for testing.

The message format is independent of the model used, so you can use messages in different agents, or the same agent with different models.

In the example below, we reuse the message from the first agent run, which uses the openai:gpt-5.2 model, in a second agent run using the google-gla:gemini-3-pro-preview model.


With Pydantic AI Gateway
Directly to Provider API
Learn about GatewayReusing messages with a different model

from pydantic_ai import Agent

agent = Agent('gateway/openai:gpt-5.2', instructions='Be a helpful assistant.')

result1 = agent.run_sync('Tell me a joke.')
print(result1.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.

result2 = agent.run_sync(
    'Explain?',
    model='google-gla:gemini-3-pro-preview',
    message_history=result1.new_messages(),
)
print(result2.output)
#> This is an excellent joke invented by Samuel Colvin, it needs no explanation.

print(result2.all_messages())
"""
[
    ModelRequest(
        parts=[
            UserPromptPart(
                content='Tell me a joke.',
                timestamp=datetime.datetime(...),
            )
        ],
        timestamp=datetime.datetime(...),
        instructions='Be a helpful assistant.',
        run_id='...',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='Did you hear about the toothpaste scandal? They called it Colgate.'
            )
        ],
        usage=RequestUsage(input_tokens=55, output_tokens=12),
        model_name='gpt-5.2',
        timestamp=datetime.datetime(...),
        run_id='...',
    ),
    ModelRequest(
        parts=[
            UserPromptPart(
                content='Explain?',
                timestamp=datetime.datetime(...),
            )
        ],
        timestamp=datetime.datetime(...),
        instructions='Be a helpful assistant.',
        run_id='...',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='This is an excellent joke invented by Samuel Colvin, it needs no explanation.'
            )
        ],
        usage=RequestUsage(input_tokens=56, output_tokens=26),
        model_name='gemini-3-pro-preview',
        timestamp=datetime.datetime(...),
        run_id='...',
    ),
]
"""

Processing Message History
Sometimes you may want to modify the message history before it's sent to the model. This could be for privacy reasons (filtering out sensitive information), to save costs on tokens, to give less context to the LLM, or custom processing logic.

Pydantic AI provides a history_processors parameter on Agent that allows you to intercept and modify the message history before each model request.

History processors replace the message history

History processors replace the message history in the state with the processed messages, including the new user prompt part. This means that if you want to keep the original message history, you need to make a copy of it.

History processors can affect new_messages() results

new_messages() determines which messages belong to the current run after all history processors have been applied. If your processor reorders, inserts, or removes messages, the set of messages returned by new_messages() may differ from what you expect.

To avoid surprises:

Preserve run_id on existing messages.
When creating new messages in a processor that should be part of the current run, use a context-aware processor and set run_id=ctx.run_id on the new message.
Reordering or removing messages may shift the boundary between "old" and "new" messages, test with new_messages() to verify the behavior matches your expectations.
Usage
The history_processors is a list of callables that take a list of ModelMessage and return a modified list of the same type.

Each processor is applied in sequence, and processors can be either synchronous or asynchronous.


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaysimple_history_processor.py

from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)


def filter_responses(messages: list[ModelMessage]) -> list[ModelMessage]:
    """Remove all ModelResponse messages, keeping only ModelRequest messages."""
    return [msg for msg in messages if isinstance(msg, ModelRequest)]

# Create agent with history processor
agent = Agent('gateway/openai:gpt-5.2', history_processors=[filter_responses])

# Example: Create some conversation history
message_history = [
    ModelRequest(parts=[UserPromptPart(content='What is 2+2?')]),
    ModelResponse(parts=[TextPart(content='2+2 equals 4')]),  # This will be filtered out
]

# When you run the agent, the history processor will filter out ModelResponse messages
# result = agent.run_sync('What about 3+3?', message_history=message_history)

Keep Only Recent Messages
You can use the history_processor to only keep the recent messages:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaykeep_recent_messages.py

from pydantic_ai import Agent, ModelMessage


async def keep_recent_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    """Keep only the last 5 messages to manage token usage."""
    return messages[-5:] if len(messages) > 5 else messages

agent = Agent('gateway/openai:gpt-5.2', history_processors=[keep_recent_messages])

# Example: Even with a long conversation history, only the last 5 messages are sent to the model
long_conversation_history: list[ModelMessage] = []  # Your long conversation history here
# result = agent.run_sync('What did we discuss?', message_history=long_conversation_history)

Be careful when slicing the message history

When slicing the message history, you need to make sure that tool calls and returns are paired, otherwise the LLM may return an error. For more details, refer to this GitHub issue.

RunContext parameter
History processors can optionally accept a RunContext parameter to access additional information about the current run, such as dependencies, model information, and usage statistics:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaycontext_aware_processor.py

from pydantic_ai import Agent, ModelMessage, RunContext


def context_aware_processor(
    ctx: RunContext[None],
    messages: list[ModelMessage],
) -> list[ModelMessage]:
    # Access current usage
    current_tokens = ctx.usage.total_tokens

    # Filter messages based on context
    if current_tokens > 1000:
        return messages[-3:]  # Keep only recent messages when token usage is high
    return messages

agent = Agent('gateway/openai:gpt-5.2', history_processors=[context_aware_processor])

This allows for more sophisticated message processing based on the current state of the agent run.

Summarize Old Messages
Use an LLM to summarize older messages to preserve context while reducing tokens.


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaysummarize_old_messages.py

from pydantic_ai import Agent, ModelMessage

# Use a cheaper model to summarize old messages.
summarize_agent = Agent(
    'gateway/openai:gpt-5-mini',
    instructions="""
Summarize this conversation, omitting small talk and unrelated topics.
Focus on the technical discussion and next steps.
""",
)


async def summarize_old_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    # Summarize the oldest 10 messages
    if len(messages) > 10:
        oldest_messages = messages[:10]
        summary = await summarize_agent.run(message_history=oldest_messages)
        # Return the last message and the summary
        return summary.new_messages() + messages[-1:]

    return messages


agent = Agent('gateway/openai:gpt-5.2', history_processors=[summarize_old_messages])

Be careful when summarizing the message history

When summarizing the message history, you need to make sure that tool calls and returns are paired, otherwise the LLM may return an error. For more details, refer to this GitHub issue, where you can find examples of summarizing the message history.

Testing History Processors
You can test what messages are actually sent to the model provider using FunctionModel:

test_history_processor.py

import pytest

from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel


@pytest.fixture
def received_messages() -> list[ModelMessage]:
    return []


@pytest.fixture
def function_model(received_messages: list[ModelMessage]) -> FunctionModel:
    def capture_model_function(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        # Capture the messages that the provider actually receives
        received_messages.clear()
        received_messages.extend(messages)
        return ModelResponse(parts=[TextPart(content='Provider response')])

    return FunctionModel(capture_model_function)


def test_history_processor(function_model: FunctionModel, received_messages: list[ModelMessage]):
    def filter_responses(messages: list[ModelMessage]) -> list[ModelMessage]:
        return [msg for msg in messages if isinstance(msg, ModelRequest)]

    agent = Agent(function_model, history_processors=[filter_responses])

    message_history = [
        ModelRequest(parts=[UserPromptPart(content='Question 1')]),
        ModelResponse(parts=[TextPart(content='Answer 1')]),
    ]

    agent.run_sync('Question 2', message_history=message_history)
    assert received_messages == [
        ModelRequest(parts=[UserPromptPart(content='Question 1')]),
        ModelRequest(parts=[UserPromptPart(content='Question 2')]),
    ]
Multiple Processors
You can also use multiple processors:


With Pydantic AI Gateway
Directly to Provider API
Learn about Gatewaymultiple_history_processors.py

from pydantic_ai import Agent, ModelMessage, ModelRequest


def filter_responses(messages: list[ModelMessage]) -> list[ModelMessage]:
    return [msg for msg in messages if isinstance(msg, ModelRequest)]


def summarize_old_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    return messages[-5:]


agent = Agent('gateway/openai:gpt-5.2', history_processors=[filter_responses, summarize_old_messages])

In this case, the filter_responses processor will be applied first, and the summarize_old_messages processor will be applied