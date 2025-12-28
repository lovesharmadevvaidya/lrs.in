Firestore schema

collections:

quizzes (collection)
 - {quiz_id} (document)
   - title: string
   - subject: string
   - time_per_question: int
   - is_premium: bool
   - questions: array of objects
     - question_text: string
     - options: array[string] (length 4)
     - correct_index: int (0-3)

results (collection)
 - {result_id} (document)
   - user_id: int
   - quiz_id: string
   - score: int
   - timestamp: int (epoch)
   - time_taken: int (seconds)

quiz_drafts (collection)
 - {admin_id} (document)
   - draft fields same as quizzes while building

users (collection)
 - {user_id} (document)
   - is_premium: bool

Notes:
- Leaderboard queries read `results` and aggregate on the backend.
- For heavy loads, pre-computed leaderboard collection or Redis sorted sets are recommended.
