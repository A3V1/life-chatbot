# System Explanation: Stateful Life Insurance Chatbot

This document provides a comprehensive explanation of the stateful life insurance chatbot system. It covers the architecture, workflow, key components, and the integration of technologies like LangChain, MySQL, and Pinecone.

## 1. High-Level Overview

The system is a sophisticated, multi-turn conversational AI designed to simulate an interaction with a human insurance advisor. It guides users through the process of selecting and understanding life insurance policies in a stateful manner, meaning it remembers context and user preferences across multiple interactions.

**Core Technologies:**

*   **Backend:** Python with FastAPI for creating a robust API.
*   **AI/LLM Orchestration:** LangChain for managing prompts, memory, and conversational chains.
*   **Language Model:** Mistral (via OpenRouter) for natural language understanding and generation.
*   **Database:** MySQL for storing structured data like policy details, user information, and chat logs.
*   **Vector Store:** Pinecone for high-speed semantic search on unstructured policy data (Retrieval-Augmented Generation - RAG).
*   **Frontend:** React (via Vite) for a modern, responsive user interface.

## 2. System Architecture & Components

The architecture is divided into a frontend, a backend, a database, and a vector store, ensuring a clean separation of concerns.

```mermaid
graph TD
    subgraph User Interface
        A[React Frontend]
    end

    subgraph Backend Server (FastAPI)
        B[API Endpoint /chat]
        C[LangChain Core: cbot.py]
        D[Data Ingestion: embed_data.py]
        E[Database Connector: sqlconnect.py]
        F[Vector Store Handler: pinecone_handler.py]
    end

    subgraph Data Layer
        G[MySQL Database]
        H[Pinecone Vector Store]
    end

    subgraph External Services
        I[LLM Service (OpenRouter/Mistral)]
    end

    A -- HTTP Request --> B
    B -- Query --> C
    C -- Retrieves Docs --> H
    C -- Sends Prompt --> I
    I -- LLM Response --> C
    C -- Returns Answer --> B
    B -- HTTP Response --> A

    D -- Reads from --> G
    D -- Writes to --> H
    E -- Connects to --> G
    F -- Connects to --> H
    F -- Prepares Docs from --> G
```

### 2.1. Frontend (`ui/`)

*   **Framework:** React with Vite.
*   **Purpose:** Provides the chat interface for the user. It captures user input and sends it to the backend via HTTP requests. It then displays the chatbot's responses.
*   **Key Files:**
    *   `src/App.jsx`: The main application component.
    *   `src/components/chatwidget.jsx`: The chat widget UI.
    *   `package.json`: Defines project dependencies like `react` and scripts to run (`dev`, `build`).

### 2.2. Backend (`back/`)

The backend is the brain of the operation, handling all the core logic.

*   **Framework:** FastAPI.
*   **Purpose:** Exposes an API that the frontend can communicate with. It orchestrates the conversational flow, data retrieval, and interaction with the LLM.
*   **Key Files:**
    *   **`main.py`**: Defines the FastAPI application and the `/chat` endpoint. It receives the user's query and passes it to the chatbot logic.
    *   **`cbot.py`**: This is the heart of the AI.
        *   It initializes the `ConversationalRetrievalChain` from LangChain.
        *   **LLM:** It configures the `ChatOpenAI` wrapper to use the `mistralai/mistral-small` model through the OpenRouter API, which acts as a gateway to various LLMs.
        *   **Memory:** It uses `ConversationBufferMemory` to store the history of the conversation, allowing the chatbot to be stateful and refer to previous messages.
        *   **Retriever:** It uses a Pinecone vector store as its retriever. When a user asks a question, the retriever finds the most relevant policy documents from Pinecone based on semantic similarity.
        *   **Prompt Template:** It uses a carefully crafted prompt template to instruct the LLM on how to behave (as an insurance agent), how to use the retrieved context, and how to format its answer.
    *   **`pinecone_handler.py`**:
        *   Connects to the Pinecone service using the API key from the `.env` file.
        *   Fetches raw policy data from MySQL using `sqlconnect.py`.
        *   Processes and formats this data into a readable `page_content` string for each policy.
        *   Uses a HuggingFace embedding model (`BAAI/bge-small-en-v1.5`) to convert the policy text into numerical vectors.
        *   Uploads these vectors to the specified Pinecone index. This process is what enables the RAG functionality.
    *   **`embed_data.py`**: A utility script to trigger the data embedding process, moving data from MySQL to Pinecone.
    *   **`sqlconnect.py`**: A simple module to handle the connection to the MySQL database and fetch data from the `policy_catalog` table.
    *   **`.env`**: Stores all secrets and configuration variables, such as API keys and database credentials, keeping them separate from the source code.

### 2.3. Data Layer

*   **MySQL Database**:
    *   **Purpose:** Acts as the primary source of truth for structured data. The `policy_catalog` table contains detailed, factual information about each insurance policy. Other tables (`user_context`, `user_info`, `lead_capture`) are designed to persist user state and capture leads.
*   **Pinecone Vector Store**:
    *   **Purpose:** Stores vector embeddings of the insurance policies. This allows for efficient semantic search. Instead of matching keywords, it matches based on meaning, which is crucial for understanding user intent (e.g., "a plan to protect my family" can be matched with policies that have "family protection" as a key feature).

### 2.4. Database Schema

The MySQL database is structured to manage user data, context, leads, and conversation history.

*   **`user_info`**: Stores basic information about the user.
    ```sql
    CREATE TABLE user_info (
      user_id VARCHAR(100) PRIMARY KEY,
      name VARCHAR(100),
      phone VARCHAR(15),
      email VARCHAR(100),
      age INT,
      income BIGINT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ```

*   **`user_context`**: Persists the state of the conversation for each user, enabling stateful interactions.
    ```sql
    CREATE TABLE user_context (
      user_id VARCHAR(100) PRIMARY KEY,
      user_intent VARCHAR(50),
      insurance_goal VARCHAR(100),
      coverage_required BIGINT,
      term_length VARCHAR(20),
      budget BIGINT,
      age INT,
      income BIGINT,
      recommended_policy_type VARCHAR(50),
      selected_policy VARCHAR(100),
      context_state ENUM(
        'intent_identified',
        'goal_identified',
        'profile_captured',
        'policy_type_suggested',
        'policy_recommended',
        'policy_detail_shown',
        'application_started',
        'completed'
      ),
      last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES user_info(user_id)
    );
    ```

*   **`lead_capture`**: Stores information when a user expresses interest in applying for a policy or speaking to an advisor.
    ```sql
    CREATE TABLE lead_capture (
      lead_id INT AUTO_INCREMENT PRIMARY KEY,
      user_id VARCHAR(100),
      policy_id VARCHAR(50),
      contact_method ENUM('phone', 'email', 'callback'),
      contact_value VARCHAR(100),
      status ENUM('new', 'contacted', 'closed') DEFAULT 'new',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES user_info(user_id),
      FOREIGN KEY (policy_id) REFERENCES policy_catalog(policy_id)
    );
    ```

*   **`chat_log`**: Optionally logs every message exchanged between the user and the bot for analysis and debugging.
    ```sql
    CREATE TABLE chat_log (
      log_id INT AUTO_INCREMENT PRIMARY KEY,
      user_id VARCHAR(100),
      message_type ENUM('user', 'bot'),
      message TEXT,
      timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES user_info(user_id)
    );
    ```

## 3. Step-by-Step Workflow (A Typical Conversation)

1.  **User Input**: A user types a message like "I'm 30 and need a 1Cr cover for 30 years" into the React frontend.
2.  **API Request**: The frontend sends a POST request to the `/chat` endpoint of the FastAPI backend with the user's message as the `query`.
3.  **Chain Invocation**: The `main.py` file receives the request and calls the `bot.ask()` method in `cbot.py`.
4.  **Memory & History**: The `ConversationalRetrievalChain` first looks at the `ConversationBufferMemory` to load the history of the current conversation.
5.  **Context Retrieval (RAG)**:
    *   The chain takes the current user query ("I'm 30 and need a 1Cr cover for 30 years") and potentially the chat history to form a search query.
    *   It passes this query to the **Pinecone retriever**.
    *   The retriever searches the Pinecone index for policy documents that are semantically closest to the user's needs. It might retrieve 2-3 top matching policies.
6.  **Prompt Assembly**: The chain combines:
    *   The retrieved policy documents (the `context`).
    *   The user's original question (`question`).
    *   The chat history (`chat_history`).
    *   The instructions from the `PromptTemplate`.
7.  **LLM Inference**: The fully assembled prompt is sent to the Mistral LLM via the OpenRouter API.
8.  **Response Generation**: The LLM processes the prompt and generates a human-like response, such as: "Based on your age and requirements, here are two term insurance plans that fit your needs: [Policy A details] and [Policy B details]. Both offer a ₹1Cr cover within your budget."
9.  **Memory Update**: The user's question and the bot's answer are saved back into the `ConversationBufferMemory`.
10. **API Response**: The final answer is sent back to the frontend as a JSON response.
11. **UI Update**: The React frontend displays the chatbot's answer to the user.

## 4. Why This System is Useful

*   **Stateful & Context-Aware:** By using memory, the chatbot can handle complex, multi-turn conversations. It doesn't treat each query in isolation, leading to a more natural and effective user experience.
*   **Accurate & Factual:** The RAG approach grounds the LLM's responses in real data from the `policy_catalog` table. This prevents the LLM from "hallucinating" or making up policy details, ensuring the information provided is accurate.
*   **Scalable:** The separation of the frontend, backend, and data layer allows each component to be scaled independently. The use of a robust database like MySQL and a dedicated vector store like Pinecone ensures performance.
*   **Flexible:** Using LangChain and a service like OpenRouter makes it easy to swap out components. You could change the LLM, the embedding model, or the vector store with minimal code changes.
*   **Simulates Human Interaction:** The entire flow is designed to replicate how a real advisor works: understanding needs, asking clarifying questions, retrieving relevant options, and presenting them clearly.

This architecture provides a powerful and flexible foundation for building a truly intelligent and helpful life insurance chatbot.
