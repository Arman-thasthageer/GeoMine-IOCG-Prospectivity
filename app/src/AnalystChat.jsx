
import React, { useState } from "react";

export default function AnalystChat() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Welcome to GeoMine Grounded Analyst! Ask me about prospectivity scores, geological targets, deposits, or grid cells."
    }
  ]);
  const [loading, setLoading] = useState(false);

  const suggestions = [
    "Which target has the highest score?",
    "Tell me about R2",
    "How many targets are available?",
    "How many known deposits are in the targets?",
    "Explain Grid FID 2"
  ];

  async function sendQuestion(value = question) {
    const text = value.trim();
    if (!text || loading) return;

    setMessages(prev => [...prev, { role: "user", text }]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "API request failed");
      }

      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          text: data.answer,
          grounded: data.grounded,
          sources: data.sources || []
        }
      ]);
    } catch (error) {
      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          text: `Unable to contact GeoMine API: ${error.message}`
        }
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="analyst-chat">
      <div className="analyst-header">
        <div>
          <h2>GeoMine Grounded Analyst</h2>
          <p>Ask questions about your geological prospectivity data</p>
        </div>
        <span className="analyst-status">API Ready</span>
      </div>

      <div className="analyst-suggestions">
        {suggestions.map((item, index) => (
          <button
            key={index}
            onClick={() => sendQuestion(item)}
            disabled={loading}
          >
            {item}
          </button>
        ))}
      </div>

      <div className="analyst-messages">
        {messages.map((message, index) => (
          <div key={index} className={`analyst-message ${message.role}`}>
            <strong>
              {message.role === "user" ? "You" : "GeoMine Analyst"}
            </strong>
            <p>{message.text}</p>

            {message.grounded !== undefined && (
              <small>
                Grounded response: {message.grounded ? "Yes" : "No"}
              </small>
            )}

            {message.sources?.length > 0 && (
              <small>Sources: {message.sources.join(", ")}</small>
            )}
          </div>
        ))}

        {loading && (
          <p className="analyst-loading">
            Retrieving information from GeoMine...
          </p>
        )}
      </div>

      <form
        className="analyst-input-area"
        onSubmit={event => {
          event.preventDefault();
          sendQuestion();
        }}
      >
        <input
          value={question}
          onChange={event => setQuestion(event.target.value)}
          placeholder="Ask about a target or grid cell..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !question.trim()}>
          Send
        </button>
      </form>

      <p className="analyst-note">
        PU scores are ranking scores, not calibrated probabilities.
        Unlabelled cells are not confirmed negative locations.
      </p>
    </section>
  );
}
