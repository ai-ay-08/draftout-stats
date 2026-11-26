import { useState } from 'react'

/*
    Set up the frontend. Send a POST request
    to the backend with the username, and display the match history.
*/

export default function App() {
    const [username, setUsername] = useState('')
    const [matches, setMatches] = useState([])

    async function handleSubmit(event) {
        event.preventDefault()

        const response = await fetch('/api/matches', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username })
        })

        const data = await response.json()

        if (response.ok) {
            setMatches(data.matches)
        }
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

            <ul>
                {matches.map((match, index) => (
                    <li key={`${match.matchId}-${index}`}>
                        Match {match.matchId}: {match.outcome} {match.score} vs {' '}
                        {match.opponent} (rating change: {match.ratingChange})
                    </li>
                ))}
            </ul>
        </main>
    )
}