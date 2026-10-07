import { type FormEvent, useState } from "react";

import "./App.css";



type Page = "home" | "assessment" | "mental" | "auth";

type AuthUser = {
  id: number;
  name: string;
  email: string;
};



type Prediction = {

  disease: string;

  confidence: number;

};



type AnalysisResult = {

  condition: string;

  confidence: number;

  matched_symptoms: string[];

  top_predictions: Prediction[];

  disclaimer: string;
  health_response: string;
  is_emergency: boolean;
  safety_message: string;
  priority: string;

};



type ChatMessage = {

  role: "ai" | "user";

  text: string;

};



const followUpQuestions = [

  "Fever, cough ya doosre symptoms kab se hain?",

  "Symptoms mild, moderate ya severe hain?",

  "Kya aapko breathing difficulty ya chest pain ho raha hai?",

];



const defaultDisclaimer =

  "This is an informational screening-support result and not a medical diagnosis.";



const asRecord = (value: unknown): Record<string, unknown> | null => {

  if (typeof value === "object" && value !== null && !Array.isArray(value)) {

    return value as Record<string, unknown>;

  }



  return null;

};



const getResponseMessage = (data: unknown) => {

  const response = asRecord(data);



  if (!response) {

    return null;

  }



  for (const key of ["detail", "message", "error"]) {

    const message = response[key];



    if (typeof message === "string" && message.trim()) {

      return message;

    }

  }



  return null;

};



const normalizeAnalysisResult = (data: unknown): AnalysisResult => {

  const response = asRecord(data);



  if (!response || (response.status !== "success" && response.status !== "urgent")) {

    throw new Error(

      getResponseMessage(data) || "Unable to generate the screening result."

    );

  }



  const matchedSymptoms = Array.isArray(response.matched_symptoms)

    ? response.matched_symptoms.filter(

        (symptom): symptom is string => typeof symptom === "string"

      )

    : [];



  const predictions = Array.isArray(response.top_predictions)

    ? response.top_predictions

        .map((prediction) => {

          const item = asRecord(prediction);

          const disease = item?.disease;

          const confidence = Number(item?.confidence);



          if (

            typeof disease !== "string" ||

            !disease.trim() ||

            !Number.isFinite(confidence)

          ) {

            return null;

          }



          return { disease, confidence };

        })

        .filter((prediction): prediction is Prediction => prediction !== null)

    : [];



  const possibleCategories = Array.isArray(response.possible_categories)

    ? response.possible_categories.filter(

        (category): category is string => typeof category === "string"

      )

    : [];



  const topPredictions =

    predictions.length > 0

      ? predictions

      : possibleCategories.map((disease) => ({ disease, confidence: 0 }));

  const suppliedCondition = response.condition;

  const confidence = Number(response.confidence);



  return {

    condition:

      typeof suppliedCondition === "string" && suppliedCondition.trim()

        ? suppliedCondition

        : topPredictions[0]?.disease || "No specific condition identified",

    confidence: Number.isFinite(confidence)

      ? confidence

      : topPredictions[0]?.confidence || 0,

    matched_symptoms: matchedSymptoms,

    top_predictions: topPredictions,

    disclaimer:

      typeof response.disclaimer === "string" && response.disclaimer.trim()

        ? response.disclaimer

        : defaultDisclaimer,

  };

};



function App() {

  const [page, setPage] = useState<Page>("home");

  const [authMode, setAuthMode] = useState<"login" | "register">("login");



  // ============================================================

  // AUTHENTICATION FORM STATES

  // ============================================================



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




  // ============================================================

  // CONVERSATIONAL ASSESSMENT STATE

  // ============================================================



  const [symptoms, setSymptoms] = useState("");

  const [chatStarted, setChatStarted] = useState(false);

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);

  const [followUpIndex, setFollowUpIndex] = useState(0);

  const [conversationAnswers, setConversationAnswers] = useState<string[]>(

    []

  );

  const [initialSymptoms, setInitialSymptoms] = useState("");

  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const [analysisResult, setAnalysisResult] =

    useState<AnalysisResult | null>(null);

  const [analysisError, setAnalysisError] = useState("");

  // ============================================================

  // ============================================================
  // MENTAL HEALTH ASSESSMENT STATE
  // ============================================================

  const [mentalQuestions, setMentalQuestions] = useState<string[]>([]);
  const [mentalAnswers, setMentalAnswers] = useState<number[]>([]);
  const [mentalResult, setMentalResult] =
    useState<Record<string, unknown> | null>(null);
  const [mentalLoading, setMentalLoading] = useState(false);
  const [mentalError, setMentalError] = useState("");

  const API_BASE = "http://127.0.0.1:8000";


  // AUTH NAVIGATION

  // ============================================================



  const openAuth = (mode: "login" | "register") => {

    setAuthMode(mode);

    setAuthError("");

    setAuthMessage("");

    setPage("auth");

  };



  // ============================================================

  // AUTH SUBMIT

  // ============================================================



  const handleAuthSubmit = async (event: FormEvent<HTMLFormElement>) => {
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
      const endpoint = authMode === "register" ? "/register" : "/login";
      const payload =
        authMode === "register"
          ? { name: name.trim(), email: email.trim(), password }
          : { email: email.trim(), password };

      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data: unknown = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          getResponseMessage(data) ||
            (authMode === "register"
              ? "Unable to create your account."
              : "Unable to sign in.")
        );
      }

      const record = asRecord(data);
      const userRecord = asRecord(record?.user);

      if (!userRecord) {
        throw new Error(
          "Authentication succeeded but no user profile was returned."
        );
      }

      const user: AuthUser = {
        id: Number(userRecord.id),
        name: typeof userRecord.name === "string" ? userRecord.name : "User",
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
          : "Welcome back."
      );

      setTimeout(() => setPage("home"), 350);
    } catch (error) {
      console.error("Authentication error:", error);
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
    setAuthMessage("");
    setAuthError("");
  };

  const openMentalHealth = async () => {
    setPage("mental");
    setMentalError("");
    setMentalResult(null);

    if (mentalQuestions.length > 0) return;

    setMentalLoading(true);

    try {
      const response = await fetch(`${API_BASE}/mental-health/questions`);
      const data: unknown = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          getResponseMessage(data) || "Unable to load questions."
        );
      }

      const record = asRecord(data);
      const questions = Array.isArray(record?.questions)
        ? record.questions.filter(
            (question): question is string => typeof question === "string"
          )
        : [];

      if (!questions.length) {
        throw new Error("No mental-health questions were returned.");
      }

      setMentalQuestions(questions);
      setMentalAnswers(new Array(questions.length).fill(0));
    } catch (error) {
      setMentalError(
        error instanceof Error
          ? error.message
          : "Unable to load the mental-health assessment."
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
      const response = await fetch(`${API_BASE}/mental-health-assessment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers: mentalAnswers }),
      });

      const data: unknown = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          getResponseMessage(data) || "Unable to calculate the assessment."
        );
      }

      setMentalResult(asRecord(data));
    } catch (error) {
      setMentalError(
        error instanceof Error
          ? error.message
          : "Unable to calculate the assessment."
      );
    } finally {
      setMentalLoading(false);
    }
  };



  // CONVERSATIONAL SYMPTOM ASSESSMENT

  // ============================================================



  const resetAssessment = () => {

    setSymptoms("");

    setChatStarted(false);

    setChatMessages([]);

    setFollowUpIndex(0);

    setConversationAnswers([]);

    setInitialSymptoms("");

    setIsAnalyzing(false);

    setAnalysisResult(null);

    setAnalysisError("");

  };



  const handleAssessmentSubmit = async () => {

    const input = symptoms.trim();



    if (!input) {

      setAnalysisError(

        chatStarted ? "Please answer the question first." : "Please describe your symptoms first."

      );

      return;

    }



    setAnalysisError("");



    if (!chatStarted) {

      setInitialSymptoms(input);

      setChatStarted(true);

      setFollowUpIndex(0);

      setConversationAnswers([]);

      setAnalysisResult(null);

      setChatMessages([

        { role: "user", text: input },

        {

          role: "ai",

          text: "Thank you for sharing that. I will ask three quick questions before preparing your screening result.",

        },

        { role: "ai", text: followUpQuestions[0] },

      ]);

      setSymptoms("");

      return;

    }



    const updatedAnswers = [...conversationAnswers, input];

    const nextQuestionIndex = followUpIndex + 1;



    if (nextQuestionIndex < followUpQuestions.length) {

      setConversationAnswers(updatedAnswers);

      setFollowUpIndex(nextQuestionIndex);

      setChatMessages([

        ...chatMessages,

        { role: "user", text: input },

        { role: "ai", text: followUpQuestions[nextQuestionIndex] },

      ]);

      setSymptoms("");

      return;

    }



    setIsAnalyzing(true);



    try {

      const completeInput = [initialSymptoms, ...updatedAnswers].join(". ");

      const response = await fetch(`${API_BASE}/analyze-symptoms`, {

        method: "POST",

        headers: {

          "Content-Type": "application/json",

        },

        body: JSON.stringify({ symptoms: completeInput }),

      });

      const data: unknown = await response.json().catch(() => null);



      if (!response.ok) {

        throw new Error(

          getResponseMessage(data) || "Unable to generate the screening result."

        );

      }



      const result = normalizeAnalysisResult(data);



      setConversationAnswers(updatedAnswers);

      setChatMessages([

        ...chatMessages,

        { role: "user", text: input },

        {

          role: "ai",

          text: "Thank you. I have enough information to generate your screening result.",

        },

      ]);

      setAnalysisResult(result);

      setSymptoms("");

    } catch (error) {

      console.error("Assessment error:", error);

      setAnalysisError(

        error instanceof Error

          ? error.message

          : "Something went wrong while analyzing your symptoms."

      );

    } finally {

      setIsAnalyzing(false);

    }

  };



  // ============================================================

  // AUTH PAGE

  // ============================================================



  if (page === "auth") {

    return (

      <div className="app auth-page">

        <header className="navbar">

          <div className="brand">

            <div className="brand-logo">A</div>



            <div>

              <h1>AYUSHMED AI</h1>

              <p>AI Health Screening Assistant</p>

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

                ? "Sign in to access your assessments and health history."

                : "Create an account to securely keep your assessments and personal history."}

            </p>



            <form onSubmit={handleAuthSubmit}>

              {authMode === "register" && (

                <div className="form-group">

                  <label htmlFor="name">Full Name</label>



                  <input

                    id="name"

                    type="text"

                    value={name}

                    onChange={(event) =>

                      setName(event.target.value)

                    }

                    placeholder="Enter your full name"

                  />

                </div>

              )}



              <div className="form-group">

                <label htmlFor="email">Email Address</label>



                <input

                  id="email"

                  type="email"

                  value={email}

                  onChange={(event) =>

                    setEmail(event.target.value)

                  }

                  placeholder="Enter your email"

                />

              </div>



              <div className="form-group">

                <label htmlFor="password">Password</label>



                <input

                  id="password"

                  type="password"

                  value={password}

                  onChange={(event) =>

                    setPassword(event.target.value)

                  }

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

                    onChange={(event) =>

                      setConfirmPassword(event.target.value)

                    }

                    placeholder="Confirm your password"

                  />

                </div>

              )}



              {authError && (

                <div className="auth-error">

                  {authError}

                </div>

              )}



              {authMessage && (

                <div className="auth-success">

                  {authMessage}

                </div>

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

                  openAuth(

                    authMode === "login"

                      ? "register"

                      : "login"

                  )

                }

              >

                {authMode === "login"

                  ? "Create account"

                  : "Sign in"}

              </button>

            </div>



            <div className="disclaimer">

              <span>🔒</span>

              Your health information will require secure access.

            </div>

          </section>

        </main>

      </div>

    );

  }



  // ============================================================
  // ============================================================
  // MENTAL HEALTH PAGE
  // ============================================================

  if (page === "mental") {
    return (
      <div className="app">
        <header className="navbar">
          <div className="brand">
            <div className="brand-logo">A</div>
            <div>
              <h1>AYUSHMED AI</h1>
              <p>AI Health Screening Assistant</p>
            </div>
          </div>

          <button className="nav-link-btn" onClick={() => setPage("home")}>
            Home
          </button>
        </header>

        <main className="assessment-page">
          <button className="back-btn" onClick={() => setPage("home")}>
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
              This structured screening uses the questions returned by the
              AYUSHMED AI backend. It is not a diagnosis and should not replace
              professional care.
            </p>

            {mentalLoading && (
              <div className="auth-success" style={{ marginTop: "22px" }}>
                Working with the AYUSHMED AI backend…
              </div>
            )}

            {mentalError && (
              <div className="auth-error" style={{ marginTop: "18px" }}>
                {mentalError}
              </div>
            )}

            {!mentalResult && mentalQuestions.length > 0 && (
              <div style={{ marginTop: "28px", textAlign: "left" }}>
                {mentalQuestions.map((question, index) => (
                  <div
                    key={question}
                    style={{
                      padding: "18px 0",
                      borderBottom: "1px solid #e7eeee",
                    }}
                  >
                    <strong style={{ display: "block", marginBottom: "12px" }}>
                      {index + 1}. {question}
                    </strong>

                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(4, 1fr)",
                        gap: "8px",
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
                          style={{ fontSize: "12px", padding: "10px" }}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}

                <button
                  className="primary-btn assessment-btn"
                  style={{ marginTop: "24px" }}
                  onClick={submitMentalHealth}
                  disabled={mentalLoading}
                >
                  {mentalLoading
                    ? "Calculating…"
                    : "Calculate Screening →"}
                </button>
              </div>
            )}

            {mentalResult && (
              <div
                style={{
                  marginTop: "28px",
                  padding: "24px",
                  borderRadius: "16px",
                  background: "#f8fffe",
                  border: "1px solid #d4eeeb",
                  textAlign: "left",
                }}
              >
                <div
                  style={{
                    color: "#078f87",
                    fontSize: "12px",
                    fontWeight: 800,
                    letterSpacing: "1.4px",
                  }}
                >
                  SCREENING RESULT
                </div>

                {Object.entries(mentalResult).map(([key, value]) => (
                  <div
                    key={key}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      gap: "20px",
                      padding: "12px 0",
                      borderBottom: "1px solid #e7eeee",
                    }}
                  >
                    <strong>{key.replace(/_/g, " ")}</strong>
                    <span style={{ textAlign: "right" }}>
                      {typeof value === "object"
                        ? JSON.stringify(value)
                        : String(value)}
                    </span>
                  </div>
                ))}

                <button
                  className="primary-btn assessment-btn"
                  style={{ marginTop: "22px" }}
                  onClick={() => {
                    setMentalResult(null);
                    setMentalQuestions([]);
                    setMentalAnswers([]);
                    openMentalHealth();
                  }}
                >
                  Take Again →
                </button>
              </div>
            )}

            {!mentalLoading &&
              !mentalError &&
              mentalQuestions.length === 0 &&
              !mentalResult && (
                <button
                  className="primary-btn assessment-btn"
                  style={{ marginTop: "24px" }}
                  onClick={openMentalHealth}
                >
                  Load Assessment →
                </button>
              )}

            <div className="disclaimer" style={{ marginTop: "24px" }}>
              <span>⚠️</span>
              If you are in immediate danger or experiencing a crisis, contact
              local emergency services or a qualified mental-health professional.
            </div>
          </section>
        </main>
      </div>
    );
  }



  // ASSESSMENT PAGE

  // ============================================================



  if (page === "assessment") {

    return (

      <div className="app">

        <header className="navbar">

          <div className="brand">

            <div className="brand-logo">A</div>



            <div>

              <h1>AYUSHMED AI</h1>

              <p>AI Health Screening Assistant</p>

            </div>

          </div>



          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {authUser && (
              <span
                style={{
                  fontSize: "13px",
                  fontWeight: 700,
                  color: "#087d76",
                }}
              >
                {authUser.name.split(" ")[0]}
              </span>
            )}
            <button
              className="nav-link-btn"
              onClick={() => setPage("home")}
            >
              Home
            </button>
          </div>

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



            <span className="badge">

              AI HEALTH ASSESSMENT

            </span>



            <h2>

              {analysisResult

                ? "Your screening result."

                : chatStarted

                  ? "A few quick questions."

                  : "Tell us what you're feeling."}

            </h2>



            <p>

              {analysisResult

                ? "Review the preliminary screening support below and start over whenever you need a new assessment."

                : chatStarted

                  ? "Please answer the question below in your own words."

                  : "Describe your symptoms naturally in any language supported by AYUSHMED AI. Explain your problem just like you would talk to a doctor."}

            </p>



            {chatMessages.length > 0 && (

              <div

                className="chat-messages"

                aria-live="polite"

                style={{

                  minHeight: "auto",

                  maxHeight: "360px",

                  overflowY: "auto",

                  padding: "20px 0",

                  textAlign: "left",

                }}

              >

                {chatMessages.map((message, index) => (

                  <div

                    className={`message ${message.role}`}

                    key={`${message.role}-${index}-${message.text}`}

                  >

                    {message.text}

                  </div>

                ))}

              </div>

            )}



            {!analysisResult && (

              <>

                <textarea

                  className="symptom-input"

                  aria-label={

                    chatStarted

                      ? "Your answer to the follow-up question"

                      : "Describe your symptoms"

                  }

                  placeholder={

                    chatStarted

                      ? "Type your answer here..."

                      : "Example: Mujhe 3 din se fever hai aur raat ko bahut khansi hoti hai..."

                  }

                  rows={chatStarted ? 3 : 6}

                  value={symptoms}

                  onChange={(event) => setSymptoms(event.target.value)}

                  disabled={isAnalyzing}

                />



                <div className="input-info">

                  <span>🌐 Multilingual input</span>

                  <span>🔒 Private assessment</span>

                </div>

              </>

            )}



            {analysisError && (

              <div

                style={{

                  marginTop: "18px",

                  padding: "14px 18px",

                  borderRadius: "12px",

                  background: "#fff4f4",

                  border: "1px solid #f0caca",

                  color: "#a33a3a",

                  textAlign: "left",

                  lineHeight: 1.5,

                }}

              >

                {analysisError}

              </div>

            )}



            {!analysisResult && (

              <button

                className="primary-btn assessment-btn"

                onClick={handleAssessmentSubmit}

                disabled={isAnalyzing}

              >

                {isAnalyzing

                  ? "Generating screening result..."

                  : !chatStarted

                    ? "Start Assessment →"

                    : followUpIndex === followUpQuestions.length - 1

                      ? "Generate screening result →"

                      : "Continue →"}

              </button>

            )}



            {/* ====================================================

                REAL AI RESULT

            ==================================================== */}



            {analysisResult && (

              <div

                style={{

                  marginTop: "28px",

                  padding: "26px",

                  borderRadius: "18px",

                  background: "#f8fffe",

                  border: "1px solid #d4eeeb",

                  textAlign: "left",

                }}

              >

                <div

                  style={{

                    fontSize: "12px",

                    fontWeight: 700,

                    letterSpacing: "1.5px",

                    color: "#078f87",

                    marginBottom: "10px",

                  }}

                >

                  AI SCREENING RESULT

                </div>



                <h3

                  style={{

                    margin: "0 0 18px",

                    fontSize: "24px",

                    color: "#111",

                  }}

                >

                  Possible condition:{" "}

                  <span style={{ color: "#07968d" }}>

                    {analysisResult.condition}

                  </span>

                </h3>



                {/* Confidence */}



                <div

                  style={{

                    padding: "14px 16px",

                    borderRadius: "12px",

                    background: "#eaf8f6",

                    marginBottom: "20px",

                  }}

                >

                  <span

                    style={{

                      display: "block",

                      fontSize: "13px",

                      color: "#557",

                      marginBottom: "4px",

                    }}

                  >

                    Model confidence

                  </span>



                  <strong

                    style={{

                      fontSize: "26px",

                      color: "#078f87",

                    }}

                  >

                    {analysisResult.confidence > 0

                      ? `${analysisResult.confidence.toFixed(2)}%`

                      : "Not available"}

                  </strong>

                </div>



                {/* Matched Symptoms */}



                <div style={{ marginBottom: "20px" }}>

                  <h4

                    style={{

                      marginBottom: "10px",

                      color: "#222",

                    }}

                  >

                    Symptoms understood

                  </h4>



                  {analysisResult.matched_symptoms.length > 0 ? (

                    <div

                      style={{

                        display: "flex",

                        flexWrap: "wrap",

                        gap: "8px",

                      }}

                    >

                      {analysisResult.matched_symptoms.map((symptom) => (

                        <span

                          className="symptom-tag"

                          key={symptom}

                          style={{

                            padding: "7px 12px",

                            borderRadius: "20px",

                            background: "#e5f7f5",

                            color: "#087d76",

                            fontSize: "13px",

                          }}

                        >

                          ✓ {symptom}

                        </span>

                      ))}

                    </div>

                  ) : (

                    <p style={{ margin: 0, color: "#687878", fontSize: "14px" }}>

                      No dataset symptoms were matched clearly.

                    </p>

                  )}

                </div>



                {/* Top Predictions */}



                <div>

                  <h4

                    style={{

                      marginBottom: "10px",

                      color: "#222",

                    }}

                  >

                    Top predictions

                  </h4>



                  {analysisResult.top_predictions.length > 0 ? (

                    <div>

                      {analysisResult.top_predictions.map(

                        (prediction, index) => (

                        <div

                          key={`${prediction.disease}-${index}`}

                          style={{

                            display: "flex",

                            justifyContent: "space-between",

                            alignItems: "center",

                            padding: "11px 0",

                            borderBottom:

                              index <

                              analysisResult.top_predictions.length - 1

                                ? "1px solid #e7eeee"

                                : "none",

                          }}

                        >

                          <span>

                            {index + 1}. {prediction.disease}

                          </span>



                          <strong>

                            {prediction.confidence > 0

                              ? `${prediction.confidence.toFixed(2)}%`

                              : "Not available"}

                          </strong>

                        </div>

                        )

                      )}

                    </div>

                  ) : (

                    <p style={{ margin: 0, color: "#687878", fontSize: "14px" }}>

                      No ranked predictions are available for this input.

                    </p>

                  )}

                </div>



                {/* Disclaimer */}



                <div

                  style={{

                    marginTop: "20px",

                    paddingTop: "16px",

                    borderTop: "1px solid #dcebea",

                    fontSize: "12px",

                    lineHeight: 1.5,

                    color: "#687878",

                  }}

                >

                  ⚠️ {analysisResult.disclaimer}

                </div>



                <button

                  className="primary-btn assessment-btn"

                  onClick={resetAssessment}

                  style={{ marginTop: "22px" }}

                >

                  Start a New Assessment →

                </button>

              </div>

            )}



            <div className="disclaimer">

              <span>✓</span>

              Preliminary screening support only — not a medical

              diagnosis.

            </div>

          </section>

        </main>

      </div>

    );

  }



  // ============================================================

  // HOME PAGE

  // ============================================================



  return (

    <div className="app">

      {/* Navbar */}



      <header className="navbar">

        <div className="brand">

          <div className="brand-logo">A</div>



          <div>

            <h1>AYUSHMED AI</h1>

            <p>AI Health Screening Assistant</p>

          </div>

        </div>
        <nav className="nav-links">
          <a href="#features">Features</a>
          <a href="#how-it-works">How it works</a>

          {authUser ? (
            <>
              <span
                style={{
                  fontSize: "13px",
                  fontWeight: 700,
                  color: "#087d76",
                  padding: "8px 4px",
                }}
              >
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

            AI-POWERED HEALTH SCREENING

          </div>



          <h2>

            Your symptoms.

            <br />

            <span>Understood naturally.</span>

          </h2>



          <p className="hero-description">

            Describe what you're experiencing in your own words

            and in a supported language. AYUSHMED AI is designed

            to understand symptoms, ask relevant follow-up

            questions and provide preliminary screening support.

          </p>



          <div className="hero-buttons">

            <button

              className="primary-btn"

              onClick={() => setPage("assessment")}

            >

              Start Health Assessment →

            </button>



            <a className="text-btn" href="#how-it-works">

              See how it works

            </a>

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



        {/* AI Preview */}



        <section className="ai-preview">

          <div className="preview-glow"></div>



          <div className="chat-card">

            <div className="chat-top">

              <div className="ai-avatar">✦</div>



              <div>

                <strong>AYUSHMED AI</strong>

                <p>Health Assistant • Online</p>

              </div>



              <div className="online-dot"></div>

            </div>



            <div className="chat-status">

              <span>

                AI is ready to understand your symptoms

              </span>

            </div>



            <div className="chat-messages">

              <div className="message ai">

                Hello! 👋

                <br />

                Tell me what you're experiencing.

              </div>



              <div className="message user">

                Mujhe 3 din se bukhar hai aur raat ko bahut khansi

                hoti hai.

              </div>



              <div className="message ai">

                I understand. When did the fever start, and are

                you experiencing any breathing difficulty?

              </div>

            </div>



            <div className="chat-input">

              <span>Describe your symptoms...</span>



              <button

                onClick={() => setPage("assessment")}

              >

                ➤

              </button>

            </div>



            <div className="chat-footer">

              <span>🌐 Any supported language</span>

              <span>🔐 Secure</span>

            </div>

          </div>

        </section>

      </main>



      {/* Quick Features */}



      <section className="quick-features" id="features">

        <div className="quick-feature">

          <span>01</span>



          <div>

            <strong>Natural Conversation</strong>



            <p>

              Talk normally instead of selecting symptoms from

              lists.

            </p>

          </div>

        </div>



        <div className="quick-feature">

          <span>02</span>



          <div>

            <strong>Smart Follow-ups</strong>



            <p>

              Relevant questions based on what you tell the

              system.

            </p>

          </div>

        </div>



        <div className="quick-feature">

          <span>03</span>



          <div>

            <strong>Safety Layer</strong>



            <p>

              Potential red flags are considered before

              screening.

            </p>

          </div>

        </div>



        <div className="quick-feature">

          <span>04</span>



          <div>

            <strong>Personal History</strong>



            <p>

              Previous assessments can be available to your

              account.

            </p>

          </div>

        </div>

      </section>



      {/* Features */}



      <section className="features-section">

        <div className="section-heading">

          <span>ONE PLATFORM</span>



          <h2>More than a symptom checker.</h2>



          <p>

            AYUSHMED AI combines conversational interaction,

            screening, mental-health assessment and personal

            health history.

          </p>

        </div>



        <div className="features">

          <div className="feature-card featured-card">

            <div className="feature-icon">💬</div>



            <h3>Conversational Symptoms</h3>



            <p>

              Explain your symptoms naturally. The system is

              designed to extract symptoms, duration, severity

              and context.

            </p>



            <span className="feature-link">

              Explore assessment →

            </span>

          </div>
          <button
            type="button"
            className="feature-card"
            onClick={openMentalHealth}
            style={{
              border: "none",
              textAlign: "left",
              font: "inherit",
              cursor: "pointer",
              width: "100%",
            }}
          >
            <div className="feature-icon">🧠</div>

            <h3>Mental Health</h3>

            <p>
              Structured mental-health screening questions can be answered
              directly through the AYUSHMED AI backend.
            </p>

            <span className="feature-link">
              Mental assessment →
            </span>
          </button>



          <div className="feature-card">

            <div className="feature-icon">📋</div>



            <h3>Assessment History</h3>



            <p>

              Logged-in users can view previous conversations

              and assessment results in one place.

            </p>



            <span className="feature-link">

              View history →

            </span>

          </div>



          <div className="feature-card">

            <div className="feature-icon">🔐</div>



            <h3>Privacy & Security</h3>



            <p>

              User accounts and health information will be

              designed with privacy and secure access in mind.

            </p>



            <span className="feature-link">

              Learn about safety →

            </span>

          </div>

        </div>

      </section>



      {/* How It Works */}



      <section className="how-section" id="how-it-works">

        <div className="section-heading">

          <span>HOW IT WORKS</span>



          <h2>From conversation to screening support.</h2>

        </div>



        <div className="steps">

          <div className="step">

            <div className="step-number">01</div>



            <h3>Describe</h3>



            <p>

              Tell AYUSHMED AI what you're experiencing in

              natural language.

            </p>

          </div>



          <div className="step">

            <div className="step-number">02</div>



            <h3>Understand</h3>



            <p>

              NLP can identify symptoms, duration, severity and

              relevant context.

            </p>

          </div>



          <div className="step">

            <div className="step-number">03</div>



            <h3>Check Safety</h3>



            <p>

              Red-flag information is considered before

              ordinary screening.

            </p>

          </div>



          <div className="step">

            <div className="step-number">04</div>



            <h3>Screen</h3>



            <p>

              A medically evaluated model can provide

              preliminary screening support.

            </p>

          </div>

        </div>

      </section>



      {/* Safety */}



      <section className="safety-section">

        <div className="safety-content">

          <span className="safety-label">

            RESPONSIBLE AI

          </span>



          <h2>

            Technology can assist.

            <br />

            Doctors make decisions.

          </h2>



          <p>

            AYUSHMED AI is designed for preliminary screening

            support. It does not replace qualified healthcare

            professionals, provide emergency care or

            independently prescribe medicines.

          </p>

        </div>



        <div className="safety-card">

          <div className="safety-icon">🛡️</div>



          <h3>Safety-first architecture</h3>



          <div className="safety-item">

            <span>✓</span>

            <p>Red-flag screening</p>

          </div>



          <div className="safety-item">

            <span>✓</span>

            <p>Transparent limitations</p>

          </div>



          <div className="safety-item">

            <span>✓</span>

            <p>Human professional oversight</p>

          </div>

        </div>

      </section>



      {/* Footer */}



      <footer className="footer">

        <div>

          <strong>AYUSHMED AI</strong>



          <p>

            AI-Based Medical Symptom Analyzer and Mental Health

            Assessment System

          </p>

        </div>



        <div className="footer-meta">

          <span>Academic Project • 2026</span>

          <span>Screening support only</span>

        </div>

      </footer>

    </div>

  );

}



export default App;

