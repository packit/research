# Agentic AI architecture

## Can we use native thinking mode of models instead of using the think tool with RequirementAgent? Would it be possible to make that work with BeeAI? If not, can we tune arguments of RequirementAgent?

LiteLLM supports translating `reasoning_effort` option into model specific reasoning/thinking configuration,
allowing to control the level of reasoning of models that support it. It also converts model thoughts
into `reasoning_content` (universal) and `thinking_blocks` (Anthropic-specific) attributes in assistant messages.

Docs: https://docs.litellm.ai/docs/reasoning_content

BeeAI doesn't support this, but implementing it is quite simple, it's just about propagating the options/attributes
and combining it with a custom middleware for instance.

So the answer is yes, this is definitely possible. However, as it turns out, Anthropic models don't support reasoning
together with tool constraints. Considering that BeeAI `RequirementAgent` is built on tool constraints
and the `ToolCallingAgent` has just been deprecated in favor of it, this means Anthropic models can't work with BeeAI
with reasoning enabled.

## Is the BeeAI's "RequirementAgent with conditions" concept best for our purposes? Do the benefits outweigh the model-specific issues with tool calls?

Without model-native reasoning enabled, I would say it is necessary. Being able to observe model thoughts is essential
for debugging. With model-native reasoning, we no longer need the `Think` tool and the benefits of the requirements
become questionable. But it's probably the only way how to force a model to call a certain tool when it tends not to do it,
and I remember some instances of this happening (upstream patch verification). That being said, even without
the `Think` tool we would still have issues with models that don't want to respect the constraints.

## Do we need a framework at all? Would it be possible to build the agents directly on top of VertexAI API? Would that bring us any benefits?

Probably not, however, using a framework gives us more flexibility if we want to switch providers in the future,
and gives us the benefits of API unification and caching. Also, I've just learned that for example Anthropic models
via VertexAI API behave a bit differently than via Anthropic API, so in case we would decide to go with
a pure VertexAI client we could be locking ourselves out from some features.

I think preserving at least LiteLLM as a low-level layer makes sense, but I believe also BeeAI has its place.
One of the biggest disadvantages is its rapid development that brings breaking changes and not keeping up with them
just makes it more difficult to adapt in the future. On the other hand, the upstream is very responsive and supportive,
paying attention to our issues even if they may not be strictly aligned with their focus.

I think we should decide on how flexible we need to be going forward and do further research, for example
trying to implement a VertexAI API client demo agent and an agent build on top of LiteLLM without BeeAI, and evaluate
pros and cons of each approach. We also need to consider the previous points (tool constraints and reasoning).

## How complicated it would be to get a more searchable solution when debugging agentic runs? Phoenix is amazing in visualizing the runs but the lack of "easy search in a text file" makes debugging longer. Also the default BeeAI Middleware prints everything which makes the output hard to consume.

It should be quite easy, just implementing a custom middleware. It could mirror what `openinference-instrumentation-beeai`
traces and Phoenix displays, or it can be something else, thanks to the BeeAI emitter system the possibilities are virtually
limitless. Even the default middleware has several filters and options that if tweaked could make it more usable,
but I think implementing a custom middleware is the way to go. It will be also necessary for logging model-native
reasoning content (see the first point).
