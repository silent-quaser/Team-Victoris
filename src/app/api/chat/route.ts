import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const { message, context } = await request.json();

    const apiKey = process.env.GROQ_API_KEY || process.env.NEXT_PUBLIC_GROQ_API_KEY;

    if (!apiKey) {
      return NextResponse.json(
        { error: 'Groq API Key not found. Please set GROQ_API_KEY in your environment variables.' },
        { status: 500 }
      );
    }

    const systemPrompt = `You are GridCopilot, an AI assistant for a power grid management platform called GridGuard.
Provide concise, professional, and helpful responses to grid operators. 
Context about the grid state:
${context ? JSON.stringify(context) : 'No context provided.'}
`;

    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'llama3-8b-8192',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: message }
        ],
        temperature: 0.5,
        max_tokens: 500
      }),
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error('Groq API Error:', errorData);
      return NextResponse.json(
        { error: 'Failed to generate response from Groq API' },
        { status: 500 }
      );
    }

    const data = await response.json();
    const botResponse = data.choices[0]?.message?.content || "I'm sorry, I couldn't process that request.";

    return NextResponse.json({ text: botResponse });
  } catch (error) {
    console.error('Chat API Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
