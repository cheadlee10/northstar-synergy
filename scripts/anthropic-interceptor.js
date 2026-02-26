/**
 * ANTHROPIC REQUEST INTERCEPTOR
 * Wraps Anthropic SDK client to log every API call automatically
 * 
 * Usage:
 * const wrapAnthropicClient = require('./anthropic-interceptor');
 * const client = new Anthropic();
 * const wrappedClient = wrapAnthropicClient(client, agentId);
 * // Now all client.messages.create() calls are logged
 */

const AnthropicUsageTracker = require('./anthropic-usage-tracker');

/**
 * Wrap an Anthropic client instance to auto-log all messages
 */
function wrapAnthropicClient(anthropicClient, agentId = 'unknown') {
  const tracker = new AnthropicUsageTracker();
  tracker.init();

  // Capture original create method
  const originalCreate = anthropicClient.messages.create.bind(anthropicClient.messages);

  // Replace with wrapped version
  anthropicClient.messages.create = async function (params) {
    const startTime = Date.now();

    try {
      // Call original method
      const response = await originalCreate(params);

      // Extract model from request
      const model = params.model || 'unknown';

      // Extract usage from response
      const inputTokens = response.usage?.input_tokens || 0;
      const outputTokens = response.usage?.output_tokens || 0;
      const requestId = response.id || null;

      // Log to tracker
      tracker.logUsage({
        agentId,
        model,
        inputTokens,
        outputTokens,
        apiRequestId: requestId,
      });

      // Attach usage to response for debugging
      response._usage_logged = true;
      response._tracker_info = {
        agentId,
        logged_at: new Date().toISOString(),
        duration_ms: Date.now() - startTime,
      };

      return response;
    } catch (err) {
      // Log errors too (for diagnostics)
      console.error(
        `[INTERCEPTOR] Error calling Anthropic (${agentId}):`,
        err.message
      );
      throw err;
    }
  };

  console.log(`[INTERCEPTOR] Wrapped Anthropic client for agent: ${agentId}`);

  return anthropicClient;
}

module.exports = wrapAnthropicClient;
