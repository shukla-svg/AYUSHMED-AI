
import { type FormEvent, useState } from "react";
import "./App.css";

type Page = "home" | "chat" | "mental" | "auth";
type AuthMode = "login" | "register";

type AuthUser = {
  id: number;
  name: string;
  email: string;
};

type ChatMessage = {
  role: "ai" | "user";
  text: string;
};

const API_BASE = "http://127.0.0.1:8000";

const asRecord = (value: unknown): Record<string, unknown> | null => {
  if (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  ) {
    return value as Record<string, unknown>;
  }
  return null;
};

const getResponseMessage = (data: unknown): string | null => {
  const record = asRecord(data);

  if (!record) return null;

  for (const key of ["detail", "message", "error"]) {
    const value = record[key];

    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }

  return null;
};

function App() {
  // Navigation
  const [page, setPage] = useState<Page>("home");

  // Authentication
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authMessage, setAuthMessage] = useState("");

  const [authUser, setAuthUser] = useState<AuthUser | null>(() => {
    try {
      const stored = localStorage.getItem("ayushmed_user");
      return stored ? (JSON.parse(stored) as AuthUser) : null;
    } catch {
      return null;
    }
  });

  // Natural AI chatbot
  const [assistantInput, setAssistantInput] = useState("");
  const [assistantMessages, setAssistantMessages] = useState<ChatMessage[]>([
    {
      role: "ai",
      text: "Namaste! 👋 Main AYUSHMED AI hoon. Aap mujhse apni health, symptoms ya general health concerns ke baare mein naturally baat kar sakte hain. Hinglish ya English, dono chalegi. Bataiye, aaj kaise hain?",
    },
  ]);

  const [assistantLoading, setAssistantLoading] = useState(false);
  const [assistantError, setAssistantError] = useState("");
  const [assistantStopped, setAssistantStopped] = useState(false);

  // Mental health assessment
  const [mentalQuestions, setMentalQuestions] = useState<string[]>([]);
  const [mentalAnswers, setMentalAnswers] = useState<number[]>([]);
  const [mentalResult, setMentalResult] =
    useState<Record<string, unknown> | null>(null);
  const [mentalLoading, setMentalLoading] = useState(false);
  const [mentalError, setMentalError] = useState("");

  // Navigation helpers
  const openChat = () => {
    setPage("chat");
  };

  const openAuth = (mode: AuthMode) => {
    setAuthMode(mode);
    setAuthError("");
    setAuthMessage("");
    setPage("auth");
  };

  // Authentication
  const handleAuthSubmit = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    setAuthError("");
    setAuthMessage("");

    if (!email.trim() || !password.trim()) {
      setAuthError("Please enter your email and password.");
      return;
    }

    if (!email.includes("@")) {
      setAuthError("Please enter a valid email address.");
      return;
    }

    if (password.length < 6) {
      setAuthError("Password must contain at least 6 characters.");
      return;
    }

    if (authMode === "register") {
      if (!name.trim()) {
        setAuthError("Please enter your full name.");
        return;
      }

      if (password !== confirmPassword) {
        setAuthError("Passwords do not match.");
        return;
      }
    }

    try {
      const endpoint =
        authMode === "register" ? "/register" : "/login";

      const payload =
        authMode === "register"
          ? {
              name: name.trim(),
              email: email.trim(),
              password,
            }
          : {
              email: email.trim(),
              password,
            };

      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data: unknown = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          getResponseMessage(data) || "Authentication failed."
        );
      }

      const record = asRecord(data);
      const userRecord = asRecord(record?.user);

      if (!userRecord) {
        throw new Error("User profile was not returned.");
      }

      const user: AuthUser = {
        id: Number(userRecord.id),
        name:
          typeof userRecord.name === "string"
            ? userRecord.name
            : "User",
        email:
          typeof userRecord.email === "string"
            ? userRecord.email
            : email.trim(),
      };

      setAuthUser(user);
      localStorage.setItem("ayushmed_user", JSON.stringify(user));

      setAuthMessage(
        authMode === "register"
          ? "Account created successfully."
          : "Welcome back!"
      );

      setPage("home");
    } catch (error) {
      setAuthError(
        error instanceof Error
          ? error.message
          : "Unable to complete authentication."
      );
    }
  };

  const logout = () => {
    localStorage.removeItem("ayushmed_user");
    setAuthUser(null);
    setPage("home");
  };

  // Chat reset
  const resetAssistantChat = () => {
    setAssistantInput("");
    setAssistantError("");
    setAssistantStopped(false);

    setAssistantMessages([
      {
        role: "ai",
        text: "Namaste! 👋 Welcome back. Aaj aap kis baare mein baat karna chahenge?",
      },
    ]);
  };

  // Natural conversational chatbot
  const sendAssistantMessage = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    const message = assistantInput.trim();

    if (
      !message ||
      assistantLoading ||
      assistantStopped
    ) {
      return;
    }

    // Keep recent conversation context
    const history = assistantMessages.slice(-12).map((item) => ({
      role: item.role === "ai" ? "assistant" : "user",
      text: item.text,
    }));

    setAssistantError("");
    setAssistantInput("");

    setAssistantMessages((current) => [
      ...current,
      {
        role: "user",
        text: message,
      },
    ]);

    setAssistantLoading(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          history,
        }),
      });

      const data: unknown = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          getResponseMessage(data) ||
            "Unable to connect to AYUSHMED AI."
        );
      }

      const record = asRecord(data);

      const reply =
        typeof record?.message === "string"
          ? record.message.trim()
          : "";

      if (!reply) {
        throw new Error(
          "The AI assistant returned an empty response."
        );
      }

      setAssistantMessages((current) => [
        ...current,
        {
          role: "ai",
          text: reply,
        },
      ]);

      // Stop only when backend explicitly indicates an urgent situation
      setAssistantStopped(record?.should_stop === true);
    } catch (error) {
      setAssistantError(
        error instanceof Error
          ? error.message
          : "Something went wrong. Please try again."
      );
    } finally {
      setAssistantLoading(false);
    }
  };

  // Mental health assessment
  const openMentalHealth = async () => {
    setPage("mental");
    setMentalError("");
    setMentalResult(null);

    if (mentalQuestions.length > 0) return;

    setMentalLoading(true);

    try {
      const response = await fetch(
        `${API_BASE}/mental-health/questions`
      );

      const data: unknown = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          getResponseMessage(data) ||
            "Unable to load questions."
        );
      }

      const record = asRecord(data);

      const questions = Array.isArray(record?.questions)
        ? record.questions.filter(
            (item): item is string => typeof item === "string"
          )
        : [];

      if (questions.length === 0) {
        throw new Error("No assessment questions were returned.");
      }

      setMentalQuestions(questions);
      setMentalAnswers(new Array(questions.length).fill(0));
    } catch (error) {
      setMentalError(
        error instanceof Error
          ? error.message
          : "Unable to load mental-health assessment."
      );
    } finally {
      setMentalLoading(false);
    }
  };

  const submitMentalHealth = async () => {
    if (mentalAnswers.length !== mentalQuestions.length) return;

    setMentalLoading(true);
    setMentalError("");

    try {
      const response = await fetch(
        `${API_BASE}/mental-health-assessment`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            answers: mentalAnswers,
          }),
        }
      );

      const data: unknown = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          getResponseMessage(data) ||
            "Unable to calculate assessment."
        );
      }

      setMentalResult(asRecord(data));
    } catch (error) {
      setMentalError(
        error instanceof Error
          ? error.message
          : "Unable to calculate assessment."
      );
    } finally {
      setMentalLoading(false);
    }
  };

  // Authentication page
  if (page === "auth") {
    return (
      <div className="app auth-page">
        <header className="navbar">
          <div className="brand">
            <div className="brand-logo">A</div>
            <div>
              <h1>AYUSHMED AI</h1>
              <p>AI Health Assistant</p>
            </div>
          </div>

          <button
            className="nav-link-btn"
            onClick={() => setPage("home")}
          >
            Home
          </button>
        </header>

        <main className="auth-container">
          <section className="auth-card">
            <div className="assessment-icon">✦</div>

            <span className="badge">
              {authMode === "login"
                ? "WELCOME BACK"
                : "CREATE ACCOUNT"}
            </span>

            <h2>
              {authMode === "login"
                ? "Welcome back."
                : "Create your account."}
            </h2>

            <p className="auth-description">
              {authMode === "login"
                ? "Sign in to access AYUSHMED AI."
                : "Create an account to get started."}
            </p>

            <form onSubmit={handleAuthSubmit}>
              {authMode === "register" && (
                <div className="form-group">
                  <label htmlFor="name">Full Name</label>
                  <input
                    id="name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter your name"
                  />
                </div>
              )}

              <div className="form-group">
                <label htmlFor="email">Email Address</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                />
              </div>

              <div className="form-group">
                <label htmlFor="password">Password</label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                />
              </div>

              {authMode === "register" && (
                <div className="form-group">
                  <label htmlFor="confirm-password">
                    Confirm Password
                  </label>
                  <input
                    id="confirm-password"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) =>
                      setConfirmPassword(e.target.value)
                    }
                    placeholder="Confirm password"
                  />
                </div>
              )}

              {authError && (
                <div className="auth-error">{authError}</div>
              )}

              {authMessage && (
                <div className="auth-success">{authMessage}</div>
              )}

              <button
                type="submit"
                className="primary-btn auth-btn"
              >
                {authMode === "login"
                  ? "Sign In →"
                  : "Create Account →"}
              </button>
            </form>

            <div className="auth-switch">
              <span>
                {authMode === "login"
                  ? "Don't have an account?"
                  : "Already have an account?"}
              </span>

              <button
                onClick={() =>
                  setAuthMode(
                    authMode === "login" ? "register" : "login"
                  )
                }
              >
                {authMode === "login"
                  ? "Create account"
                  : "Sign in"}
              </button>
            </div>
          </section>
        </main>
      </div>
    );
  }

  // Mental health page
  if (page === "mental") {
    return (
      <div className="app">
        <header className="navbar">
          <div className="brand">
            <div className="brand-logo">A</div>
            <div>
              <h1>AYUSHMED AI</h1>
              <p>AI Health Assistant</p>
            </div>
          </div>

          <button
            className="nav-link-btn"
            onClick={() => setPage("home")}
          >
            Home
          </button>
        </header>

        <main className="assessment-page">
          <button
            className="back-btn"
            onClick={() => setPage("home")}
          >
            ← Back to Home
          </button>

          <section className="assessment-card">
            <div className="assessment-icon">🧠</div>
            <span className="badge">MENTAL HEALTH SCREENING</span>

            <h2>
              {mentalResult
                ? "Your screening summary."
                : "How have you been feeling?"}
            </h2>

            <p>
              This structured assessment is not a medical
              diagnosis or a replacement for professional care.
            </p>

            {mentalLoading && (
              <div className="auth-success">
                Working with AYUSHMED AI...
              </div>
            )}

            {mentalError && (
              <div className="auth-error">{mentalError}</div>
            )}

            {!mentalResult && mentalQuestions.length > 0 && (
              <div style={{ marginTop: 28, textAlign: "left" }}>
                {mentalQuestions.map((question, index) => (
                  <div
                    key={question}
                    style={{
                      padding: "18px 0",
                      borderBottom: "1px solid #e7eeee",
                    }}
                  >
                    <strong>
                      {index + 1}. {question}
                    </strong>

                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns:
                          "repeat(2, minmax(0, 1fr))",
                        gap: 8,
                        marginTop: 12,
                      }}
                    >
                      {[
                        ["Not at all", 0],
                        ["Several days", 1],
                        ["More than half the days", 2],
                        ["Nearly every day", 3],
                      ].map(([label, value]) => (
                        <button
                          key={String(value)}
                          type="button"
                          className={
                            mentalAnswers[index] === value
                              ? "primary-btn"
                              : "nav-link-btn"
                          }
                          onClick={() => {
                            const next = [...mentalAnswers];
                            next[index] = Number(value);
                            setMentalAnswers(next);
                          }}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}

                <button
                  className="primary-btn assessment-btn"
                  onClick={submitMentalHealth}
                  disabled={mentalLoading}
                  style={{ marginTop: 24 }}
                >
                  Calculate Screening →
                </button>
              </div>
            )}

            {mentalResult && (
              <div
                style={{
                  marginTop: 28,
                  padding: 24,
                  borderRadius: 16,
                  background: "#f8fffe",
                  textAlign: "left",
                }}
              >
                <h3>Screening Result</h3>

                {Object.entries(mentalResult).map(([key, value]) => (
                  <div
                    key={key}
                    style={{
                      padding: "12px 0",
                      borderBottom: "1px solid #e7eeee",
                    }}
                  >
                    <strong>{key.replace(/_/g, " ")}: </strong>
                    {typeof value === "object"
                      ? JSON.stringify(value)
                      : String(value)}
                  </div>
                ))}

                <button
                  className="primary-btn assessment-btn"
                  style={{ marginTop: 22 }}
                  onClick={() => {
                    setMentalResult(null);
                    setMentalQuestions([]);
                    setMentalAnswers([]);
                  }}
                >
                  Take Again →
                </button>
              </div>
            )}

            <div className="disclaimer">
              ⚠️ If you are experiencing a mental-health crisis,
              contact emergency services or a qualified professional.
            </div>
          </section>
        </main>
      </div>
    );
  }

  // Natural chatbot page
  if (page === "chat") {
    return (
      <div className="app">
        <header className="navbar">
          <div className="brand">
            <div className="brand-logo">A</div>
            <div>
              <h1>AYUSHMED AI</h1>
              <p>Natural AI Health Assistant</p>
            </div>
          </div>

          <button
            className="nav-link-btn"
            onClick={() => setPage("home")}
          >
            Home
          </button>
        </header>

        <main className="assessment-page">
          <button
            className="back-btn"
            onClick={() => setPage("home")}
          >
            ← Back to Home
          </button>

          <section className="assessment-card">
            <div className="assessment-icon">✦</div>

            <span className="badge">AYUSHMED AI CHAT</span>

            <h2>Your personal health conversation.</h2>

            <p>
              Talk naturally. Share your concerns in Hinglish
              or English. No fixed questionnaire.
            </p>

            {/* Chat messages */}
            <div
              aria-live="polite"
              style={{
                marginTop: 26,
                display: "flex",
                flexDirection: "column",
                gap: 14,
                minHeight: 280,
                maxHeight: 460,
                overflowY: "auto",
                padding: 12,
                textAlign: "left",
                background: "#fbfefe",
                borderRadius: 16,
                border: "1px solid #e5eeee",
              }}
            >
              {assistantMessages.map((item, index) => (
                <div
                  key={`${item.role}-${index}`}
                  style={{
                    alignSelf:
                      item.role === "user"
                        ? "flex-end"
                        : "flex-start",
                    maxWidth: "85%",
                    padding: "13px 16px",
                    borderRadius: 15,
                    borderBottomRightRadius:
                      item.role === "user" ? 4 : 15,
                    borderBottomLeftRadius:
                      item.role === "ai" ? 4 : 15,
                    lineHeight: 1.65,
                    whiteSpace: "pre-wrap",
                    overflowWrap: "anywhere",
                    background:
                      item.role === "user"
                        ? "#078f87"
                        : "#edf7f6",
                    color:
                      item.role === "user" ? "#fff" : "#203d3a",
                  }}
                >
                  {item.text}
                </div>
              ))}

              {assistantLoading && (
                <div
                  style={{
                    alignSelf: "flex-start",
                    padding: "13px 16px",
                    borderRadius: 14,
                    background: "#edf7f6",
                    color: "#203d3a",
                  }}
                >
                  AYUSHMED AI is thinking...
                </div>
              )}
            </div>

            {assistantError && (
              <div
                className="auth-error"
                style={{ marginTop: 16 }}
              >
                {assistantError}
              </div>
            )}

            {assistantStopped && (
              <div
                className="auth-error"
                style={{ marginTop: 16 }}
              >
                This conversation has been paused because your
                message may indicate an urgent health concern.
                Please seek immediate medical assistance.
              </div>
            )}

            {/* Message input */}
            <form
              onSubmit={sendAssistantMessage}
              style={{ marginTop: 20 }}
            >
              <label
                htmlFor="assistant-message"
                className="sr-only"
              >
                Your message
              </label>

              <textarea
                id="assistant-message"
                value={assistantInput}
                onChange={(event) =>
                  setAssistantInput(event.target.value)
                }
                placeholder="Message AYUSHMED AI... (Hinglish or English)"
                rows={3}
                maxLength={1500}
                disabled={assistantLoading || assistantStopped}
                style={{
                  width: "100%",
                  resize: "vertical",
                  boxSizing: "border-box",
                }}
              />

              <button
                className="primary-btn assessment-btn"
                type="submit"
                disabled={
                  !assistantInput.trim() ||
                  assistantLoading ||
                  assistantStopped
                }
                style={{ marginTop: 12 }}
              >
                {assistantLoading
                  ? "Replying..."
                  : "Send Message →"}
              </button>
            </form>

            <button
              className="nav-link-btn"
              type="button"
              onClick={resetAssistantChat}
              style={{ marginTop: 14 }}
            >
              + Start New Conversation
            </button>

            <div className="disclaimer" style={{ marginTop: 22 }}>
              <span>⚠️</span>
              AYUSHMED AI provides informational health support,
              not a diagnosis or prescription. Severe breathing
              difficulty, chest pain, fainting or other emergency
              symptoms require immediate medical care.
            </div>
          </section>
        </main>
      </div>
    );
  }

  // Home page
  return (
    <div className="app">
      <header className="navbar">
        <div className="brand">
          <div className="brand-logo">A</div>
          <div>
            <h1>AYUSHMED AI</h1>
            <p>AI Health Assistant</p>
          </div>
        </div>

        <nav className="nav-links">
          <a href="#features">Features</a>
          <a href="#how-it-works">How it works</a>

          {authUser ? (
            <>
              <span style={{ color: "#087d76", fontWeight: 700 }}>
                Hi, {authUser.name.split(" ")[0]}
              </span>
              <button className="nav-login-btn" onClick={logout}>
                Logout
              </button>
            </>
          ) : (
            <button
              className="nav-login-btn"
              onClick={() => openAuth("login")}
            >
              Login
            </button>
          )}
        </nav>
      </header>

      {/* Hero */}
      <main className="hero">
        <section className="hero-content">
          <div className="badge">
            <span className="pulse"></span>
            AI-POWERED HEALTH ASSISTANT
          </div>

          <h2>
            Your health.
            <br />
            <span>Understood naturally.</span>
          </h2>

          <p className="hero-description">
            Talk to AYUSHMED AI just like you talk to a person.
            Describe your concerns naturally in Hinglish or
            English and get conversational health information.
          </p>

          <div className="hero-buttons">
            <button
              className="primary-btn"
              onClick={openChat}
            >
              Start Chatting →
            </button>

            <button
              className="text-btn"
              onClick={openChat}
            >
              Chat in Hinglish →
            </button>

            <button
              className="text-btn"
              onClick={openMentalHealth}
            >
              Mental Health →
            </button>
          </div>

          <div className="trust-row">
            <div>
              <strong>🌐</strong>
              <span>Multilingual</span>
            </div>
            <div>
              <strong>🧠</strong>
              <span>AI-assisted</span>
            </div>
            <div>
              <strong>🛡️</strong>
              <span>Safety-first</span>
            </div>
          </div>
        </section>

        {/* Chat preview */}
        <section className="ai-preview">
          <div className="preview-glow"></div>

          <div className="chat-card">
            <div className="chat-top">
              <div className="ai-avatar">✦</div>
              <div>
                <strong>AYUSHMED AI</strong>
                <p>Natural Health Assistant</p>
              </div>
              <div className="online-dot"></div>
            </div>

            <div className="chat-status">
              <span>AI is ready to chat with you</span>
            </div>

            <div className="chat-messages">
              <div className="message ai">
                Hello! 👋
                <br />
                Namaste! Aaj kaise hain?
              </div>

              <div className="message user">
                Mujhe aaj bukhar ho raha hai.
              </div>

              <div className="message ai">
                Oh, I understand. Aapko bukhar ho raha hai.
                Main aapki baat samajhne aur health information
                dene mein help kar sakta hoon.
              </div>
            </div>

            <div className="chat-input">
              <span>Message AYUSHMED AI...</span>
              <button onClick={openChat}>➤</button>
            </div>

            <div className="chat-footer">
              <span>🌐 Hinglish & English</span>
              <span>🔐 Privacy-conscious</span>
            </div>
          </div>
        </section>
      </main>

      {/* Features */}
      <section className="quick-features" id="features">
        <div className="quick-feature">
          <span>01</span>
          <div>
            <strong>Natural Conversation</strong>
            <p>Talk normally instead of filling out forms.</p>
          </div>
        </div>

        <div className="quick-feature">
          <span>02</span>
          <div>
            <strong>Multilingual Chat</strong>
            <p>Communicate in Hinglish or English.</p>
          </div>
        </div>

        <div className="quick-feature">
          <span>03</span>
          <div>
            <strong>Safety Layer</strong>
            <p>Emergency warning signs are considered.</p>
          </div>
        </div>

        <div className="quick-feature">
          <span>04</span>
          <div>
            <strong>Mental Health</strong>
            <p>Access a separate structured mental-health assessment.</p>
          </div>
        </div>
      </section>

      <section className="features-section">
        <div className="section-heading">
          <span>ONE PLATFORM</span>
          <h2>Your health conversation starts here.</h2>
          <p>
            Conversational AI, symptom understanding and
            mental-health screening in one platform.
          </p>
        </div>

        <div className="features">
          <button
            className="feature-card featured-card"
            onClick={openChat}
            style={{
              border: "none",
              textAlign: "left",
              font: "inherit",
              cursor: "pointer",
            }}
          >
            <div className="feature-icon">💬</div>
            <h3>Natural AI Chat</h3>
            <p>
              Explain your health concerns naturally.
              No fixed symptom questionnaire.
            </p>
            <span className="feature-link">Start chatting →</span>
          </button>

          <button
            className="feature-card"
            onClick={openMentalHealth}
            style={{
              border: "none",
              textAlign: "left",
              font: "inherit",
              cursor: "pointer",
            }}
          >
            <div className="feature-icon">🧠</div>
            <h3>Mental Health</h3>
            <p>
              Access a separate structured mental-health
              screening assessment.
            </p>
            <span className="feature-link">
              Mental assessment →
            </span>
          </button>

          <div className="feature-card">
            <div className="feature-icon">🛡️</div>
            <h3>Responsible AI</h3>
            <p>
              Safety-aware responses and clear limitations
              of AI health information.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🔐</div>
            <h3>Privacy</h3>
            <p>
              Account access and health information require
              appropriate privacy and security controls.
            </p>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="how-section" id="how-it-works">
        <div className="section-heading">
          <span>HOW IT WORKS</span>
          <h2>Simple. Natural. Conversational.</h2>
        </div>

        <div className="steps">
          <div className="step">
            <div className="step-number">01</div>
            <h3>Talk</h3>
            <p>Describe your concern in your own words.</p>
          </div>

          <div className="step">
            <div className="step-number">02</div>
            <h3>Understand</h3>
            <p>AI processes your message and conversation context.</p>
          </div>

          <div className="step">
            <div className="step-number">03</div>
            <h3>Check Safety</h3>
            <p>Potential emergency warning signs are considered.</p>
          </div>

          <div className="step">
            <div className="step-number">04</div>
            <h3>Respond</h3>
            <p>Receive conversational health information.</p>
          </div>
        </div>
      </section>

      {/* Safety */}
      <section className="safety-section">
        <div className="safety-content">
          <span className="safety-label">RESPONSIBLE AI</span>

          <h2>
            Technology can assist.
            <br />
            Doctors make decisions.
          </h2>

          <p>
            AYUSHMED AI is designed to provide informational
            health support. It does not replace qualified
            healthcare professionals, provide emergency care
            or independently prescribe medicines.
          </p>
        </div>

        <div className="safety-card">
          <div className="safety-icon">🛡️</div>
          <h3>Safety-first architecture</h3>

          <div className="safety-item">
            <span>✓</span>
            <p>Red-flag awareness</p>
          </div>

          <div className="safety-item">
            <span>✓</span>
            <p>Transparent limitations</p>
          </div>

          <div className="safety-item">
            <span>✓</span>
            <p>Professional medical guidance</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div>
          <strong>AYUSHMED AI</strong>
          <p>
            AI-Based Medical Symptom Analyzer and
            Mental Health Assessment System
          </p>
        </div>

        <div className="footer-meta">
          <span>Academic Project • 2026</span>
          <span>Informational support only</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
