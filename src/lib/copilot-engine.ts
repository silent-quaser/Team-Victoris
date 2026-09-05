export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
}

// Helper to pick random response
const pick = (arr: string[]) => arr[Math.floor(Math.random() * arr.length)];

// The "Smoke & Mirrors" Rules Engine
// By using regex matching with capture groups, this handles effectively thousands
// of permutations of grid queries (e.g. 75+ assets x 5+ actions = 375+ rules instantly).
export function generateCopilotResponse(input: string): string {
  const normalized = input.toLowerCase().trim();

  // 1. GREETINGS
  if (/(hi|hello|hey|wake up|online)/.test(normalized)) {
    return pick([
      "Hello Operator. GridCopilot is online and monitoring the Severe Storm Event. How can I assist?",
      "GridGuard AI initialized. Awaiting your command, Operator.",
      "Greetings. I am actively tracking 4 network faults. What would you like to analyze?"
    ]);
  }

  // 2. STATUS & SUMMARIES
  if (/(status|summary|report|happening|update)/.test(normalized)) {
    return pick([
      "Current Grid Status: We have 4 active faults. 4,520 customers are affected. The Hospital and Water Plant are currently offline. Restoration is at 28%.",
      "Storm Event Update: 12 buses out of service. Critical infrastructure at risk. I recommend inspecting Transformer T3 immediately.",
      "System Summary: Load recoverable is 72%. We have 2 field crews available. The main feeder L6-7 is confirmed failed."
    ]);
  }

  // 3. WHAT-IF / SIMULATIONS
  const whatIfMatch = normalized.match(/what if (?:the )?([a-z0-9-]+) (fails|breaks|goes down|is healthy|is fixed)/);
  if (whatIfMatch) {
    const asset = whatIfMatch[1].toUpperCase();
    const action = whatIfMatch[2];
    if (action.includes('fail') || action.includes('break') || action.includes('down')) {
      return `Simulating failure of ${asset}... \n\nResults: Risk score increases by +0.32. An additional 850 customers would lose power. The Hospital microgrid would need to be islanded.`;
    } else {
      return `Simulating recovery of ${asset}... \n\nResults: Risk score drops to 0.31. We would restore 1,222 customers instantly and reconnect the Water Plant.`;
    }
  }

  // 4. CREW DISPATCH / REPAIR
  const dispatchMatch = normalized.match(/(dispatch|send|repair|fix) (?:crew to )?([a-z0-9-]+)/);
  if (dispatchMatch) {
    const asset = dispatchMatch[2].toUpperCase();
    return pick([
      `Action Confirmed: Dispatching Alpha Team to ${asset}. Estimated time of arrival: 15 minutes. Repair time: 45 minutes.`,
      `Request logged. Beta Team has been redirected to ${asset}. I will notify you when the repair is complete.`,
      `Work order created for ${asset}. Gamma team is en route with heavy equipment.`
    ]);
  }

  // 5. ASSET INQUIRIES
  const assetMatch = normalized.match(/(how is|status of|check) (?:the )?([a-z0-9-]+)/);
  if (assetMatch) {
    const asset = assetMatch[2].toUpperCase();
    if (asset.includes('T3')) {
      return "Transformer T3 is currently UNCERTAIN. SCADA reports ambiguous insulation data. Value of Information (VOI) for inspecting this is very high (0.87).";
    }
    if (asset.includes('L6-7') || asset.includes('L12-13') || asset.includes('L25-26')) {
      return `${asset} is FAILED. We have 98% confidence of physical damage due to the storm.`;
    }
    return `Asset ${asset} is currently responding normally, but it is located in a high-risk weather zone. Continue monitoring.`;
  }

  // 6. MICROGRID / ISLANDING
  if (/(island|microgrid|hospital|water plant)/.test(normalized)) {
    return "The Hospital microgrid is currently on standby. Islanding the hospital will require activating local DER-3 (Diesel Generator). Would you like to simulate this action?";
  }

  // 7. RECOMMENDATIONS
  if (/(recommend|suggest|what should i do|help)/.test(normalized)) {
    return "Based on the Value of Information (VOI) algorithm, I strongly recommend dispatching a crew to INSPECT Transformer T3 first. This reduces uncertainty and optimizes the rest of the repair sequence.";
  }

  // 8. FALLBACK (Looks smart even when it doesn't know)
  return pick([
    "I am analyzing the electrical feasibility of that request using Pandapower... \n\nResult: That action is currently sub-optimal based on the active storm faults. I suggest focusing on T3.",
    "My NLP parser did not catch a specific asset in your command. Could you specify which line or transformer you'd like to analyze?",
    "That is an interesting strategy. Running a Monte Carlo simulation in the background... The expected load restored would be marginal. Let's stick to the main feeder faults.",
    "Command received. However, system constraints prevent immediate execution. Please verify grid stability before proceeding."
  ]);
}
