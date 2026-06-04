Dify CV Knowledge Base Upload Notes

Recommended Dify settings:
- Source: Import from file
- File type: TXT files from this folder
- Chunk mode: General
- Chunk delimiter: ---CHUNK_END---
- Maximum chunk length: 2000 characters
- Chunk overlap: 0 characters
- Text cleanup: collapse consecutive spaces/new lines/tabs ON
- Delete URLs and emails: OFF
- Index mode: High Quality
- Embedding model: text-embedding-3-large
- Retrieval: Vector Search
- Top K: 5 at first, then test 8 if recall is weak
- Score threshold: OFF for the first test
- Rerank: OFF for the first test

Upload plan:
1. First upload Resume_Dify_Vector_Test_50.txt and test retrieval.
2. If the test is good, upload the five Full_Part files in one batch.
3. Wait until all documents show Completed before activating or testing in Studio.

Delimiter to paste in Dify:
---CHUNK_END---
