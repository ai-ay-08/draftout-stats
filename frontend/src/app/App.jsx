import { useState } from 'react'

/*
    Set up the frontend. Send a POST request
    to the backend with the username, and display the match history.

    Or, send a POST request with username and matchId, and display the goal history for that match.
*/

export default function App() {
    const [username, setUsername] = useState('')
    const [matches, setMatches] = useState([])
    const [expandedMatchId, setExpandedMatchId] = useState(null)
    const [goalHistory, setGoalHistory] = useState([])
    const [stats, setStats] = useState(null)

    // Send a username and obtain the match history.
    async function handleSubmit(event) {
        event.preventDefault()

        setMatches([])
        setExpandedMatchId(null)
        setGoalHistory([])
        setStats(null)

        // Start both the matches request and stats request together.
        const matchesRequest = (async () => {
            const response = await fetch('/api/matches', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username }),
            })

            const data = await response.json()

            if (response.ok) {
                setMatches(data.matches ?? [])
            }
        })()
        
        const statsRequest = (async () => {
            const response = await fetch('/api/category-sample', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username }),
            })

            const data = await response.json()
            
            if (response.ok) {
                setStats(data);
            }
        })()
    }

    // Send a username and matchId and obtain the goal history for that match.
    async function handleMatchClick(match) {
        const matchId = match.matchId 

        if (expandedMatchId === matchId) {
            setExpandedMatchId(null)
            setGoalHistory([])

            return
        }

        setExpandedMatchId(matchId)
        setGoalHistory([])

        const response = await fetch('/api/match-details', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, matchId })
        })

        const data = await response.json()

        setGoalHistory(data.goalHistory ?? [])
    }

    return (
        <main>
            <h1>Draftout Stats</h1> 

            <form onSubmit={handleSubmit}>
                <label htmlFor="username">Username: </label>
                <input 
                    id="username"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                /> 
                <button type="submit">Submit</button>
            </form>

            {stats && (
                <section>
                    <h2>Category statistics for {stats.username}</h2>
                    <p>Matches sampled: {stats.matches_sampled}</p>

                    <h3>Goal appearances by category</h3>
                    <CategoryCounts counts={stats.goals_seen} />

                    <h3>Goals completed by category</h3>
                    <CategoryCounts counts={stats.goals_completed} />
                </section>
            )}

            <ul>
                {matches.map((match, index) => {
                    // Display the match history & the goal history for the selected match.

                    const isExpanded = expandedMatchId === match.matchId
                    const events = goalHistory

                    return (
                        <li key={`${match.matchId}-${index}`}>
                            <button 
                                type="button"
                                aria-expanded={isExpanded}
                                onClick={() => handleMatchClick(match)}
                            >
                                Match {match.matchId}: {match.outcome} {match.score} vs{' '}
                                {match.opponent} (rating change: {match.ratingChange})
                            </button>

                            {isExpanded && (
                                <ul>
                                    {events.map((event, eventIndex) => (
                                        <li key={`${match.matchId}-${eventIndex}`}>
                                            {event.player} completes {event.goal} in {event.time}.
                                            {' '}Score: {event.score}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </li>
                    )
                })}
            </ul>
        </main>
    )
}

// The CategoryCounts function helps display the counts for each category in HTML

function CategoryCounts({ counts = {} }) {
    const entries = Object.entries(counts)

    if (entries.length === 0) {
        return <p>No categorized goals found.</p>
    }

    return (
        <ul>
            {entries.map(([category, count]) => (
                <li key={category}>
                    {category}: {count}
                </li>
            ))}
        </ul>
    )
}