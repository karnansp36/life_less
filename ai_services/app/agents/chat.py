from crewai import Agent, Task, Crew
from app.services.llm import get_llm

def run_chat_agent(prompt: str, memory_block: str) -> str:
    llm = get_llm()

    chat_agent = Agent(
        role="Personal AI Assistant",
        goal=(
            "Be a reliable, friendly virtual admin. Use the user's short- and long-term memory. "
            "Be concise, accurate, and say when you're unsure."
        ),
        backstory=(
            "You help with planning, notes, tasks, and summaries. "
            "You personalize responses using retrieved memories."
        ),
        allow_delegation=False,
        verbose=False,
        llm=llm,
    )

    task = Task(
        description=(
            "User query: {prompt}\n\n"
            "Context (short + long term memory):\n{memory}\n\n"
            "Answer directly. If referencing past info, mention it explicitly."
        ),
        expected_output="A clear, helpful answer in plain text.",
        agent=chat_agent,
    )

    crew = Crew(agents=[chat_agent], tasks=[task], verbose=False)
    result = crew.kickoff(inputs={"prompt": prompt, "memory": memory_block})
    return result
