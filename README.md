# riddlecrumbs-bot

Posts a Riddle Crumbs reel to Instagram automatically (ramping up to 3 a day).

- `content/bank.json`: hand-written riddles, quizzes, facts and life hacks
- `bot/content.py`: posting order + auto-generated maths tricks and brain tests
- `bot/engine.py`: draws each 7-second reel
- `bot/run.py`: decides, renders, posts and refreshes the Instagram token
- `state/state.json`: progress. Set `"paused": true` to pause posting.
