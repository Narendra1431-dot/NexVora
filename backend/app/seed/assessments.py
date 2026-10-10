"""Assessment banks: diagnostic, skill, concept and coding items.

Questions are graded on the server (``engine.competency.score_attempt``). The
API strips ``correctAnswers`` and ``explanation`` before sending anything to the
browser, so a student cannot read the answer key out of the network tab.

Coding items are reviewed by a *static* checklist rubric — student code is never
executed inside the API process (see ``services/verification.py``).
"""

from __future__ import annotations

from typing import Any


def mcq(
    qid: str,
    topic: str,
    question: str,
    options: list[str],
    correct: list[int],
    explanation: str,
    qtype: str = "MCQ",
) -> dict[str, Any]:
    return {
        "id": qid,
        "type": qtype,
        "topic": topic,
        "question": question,
        "options": options,
        "correctAnswers": correct,
        "explanation": explanation,
    }


def coding(
    qid: str,
    topic: str,
    question: str,
    snippet: str,
    options: list[str],
    correct: list[int],
    explanation: str,
) -> dict[str, Any]:
    return {
        "id": qid,
        "type": "Coding",
        "topic": topic,
        "question": question,
        "codeSnippet": snippet,
        "options": options,
        "correctAnswers": correct,
        "explanation": explanation,
    }


ASSESSMENTS: list[dict[str, Any]] = [
    {
        "id": "assess-pytorch-adaptive",
        "title": "PyTorch Deep Learning & Tensor Operations Mastery",
        "category": "Skill Assessment",
        "skillId": "dl-pytorch",
        "skillName": "PyTorch Framework & Tensors",
        "difficulty": "Intermediate",
        "estimatedTime": "8 mins",
        "passingScore": 80,
        "description": "Validates custom autograd, DataLoader throughput, DDP mechanics and memory behaviour under load.",
        "questions": [
            mcq(
                "q-pt-1",
                "Autograd & Gradient Accumulation",
                "When performing gradient accumulation across 4 micro-batches in PyTorch, which sequence of calls is correct before updating optimizer parameters?",
                [
                    "Call optimizer.zero_grad() after every micro-batch loss.backward()",
                    "Call loss.backward() on each micro-batch, then optimizer.step() and optimizer.zero_grad() once every 4 batches",
                    "Call optimizer.step() after every micro-batch, and loss.backward() only on the 4th batch",
                    "Call torch.no_grad() during backward passes to prevent recursion",
                ],
                [1],
                "Gradients accumulate in the .grad buffers across iterations, so loss.backward() runs per micro-batch while optimizer.step() and optimizer.zero_grad() run once every N batches.",
            ),
            mcq(
                "q-pt-2",
                "DataLoader & Memory Throughput",
                "Which techniques directly prevent the GPU from waiting on host CPU I/O during training?",
                [
                    "Setting pin_memory=True to allocate page-locked host memory",
                    "Tuning num_workers to prefetch batches asynchronously across processes",
                    "Calling torch.cuda.empty_cache() after every mini-batch",
                    "Using non_blocking=True when moving batches to the device",
                ],
                [0, 1, 3],
                "Pinned memory, multi-worker prefetching and non-blocking transfers hide I/O latency. empty_cache() forces synchronisation and hurts throughput.",
                qtype="Multiple Select",
            ),
            coding(
                "q-pt-3",
                "Custom Autograd Function",
                "Examine the custom ReLU below. What happens when save_for_backward is omitted in forward?",
                "class CustomReLU(torch.autograd.Function):\n"
                "    @staticmethod\n"
                "    def forward(ctx, x):\n"
                "        # missing ctx.save_for_backward(x)\n"
                "        return x.clamp(min=0)\n\n"
                "    @staticmethod\n"
                "    def backward(ctx, grad_output):\n"
                "        (x,) = ctx.saved_tensors   # unpacking\n"
                "        return grad_output * (x > 0)",
                [
                    "Unpacking the empty ctx.saved_tensors tuple raises a ValueError",
                    "The output silently becomes non-differentiable without an error",
                    "GPU memory leaks because PyTorch retains the whole graph",
                    "Gradients automatically default to torch.ones_like(x)",
                ],
                [0],
                "ctx.save_for_backward() is what retains tensors for the backward pass; unpacking ctx.saved_tensors without saving raises at runtime.",
            ),
            mcq(
                "q-pt-4",
                "Distributed Training",
                "Why is torch.nn.parallel.DistributedDataParallel preferred over DataParallel for multi-GPU training?",
                [
                    "DDP spawns one process per GPU, avoiding the GIL and the single-GPU scatter/gather hotspot",
                    "DP only works with CPU tensors and cannot use NVLink",
                    "DDP automatically quantises weights to int8 during synchronisation",
                    "DP cannot backpropagate through recurrent layers",
                ],
                [0],
                "DDP is multi-process, so it sidesteps the Global Interpreter Lock and uses ring-allreduce instead of centralised scatter/gather.",
                qtype="Reasoning",
            ),
        ],
    },
    {
        "id": "assess-transformers-mastery",
        "title": "Transformer Architecture, Attention & Decoding Dynamics",
        "category": "Concept Assessment",
        "skillId": "dl-transformers",
        "skillName": "Transformer Architecture & Attention",
        "difficulty": "Intermediate",
        "estimatedTime": "10 mins",
        "passingScore": 80,
        "description": "Tests scaled dot-product attention, KV caching economics and rotary positional embeddings.",
        "questions": [
            mcq(
                "q-tr-1",
                "Scaled Dot-Product Attention",
                "Why is the Query-Key dot product scaled by 1/sqrt(d_k) before the softmax?",
                [
                    "To keep logit variance stable for large d_k, avoiding vanishing softmax gradients",
                    "To force attention weights to sum to exactly 1.0",
                    "To invert the covariance matrix of token embeddings",
                    "To normalise the output to zero mean and unit variance",
                ],
                [0],
                "Large d_k makes dot products large in magnitude, pushing softmax into a saturated region with tiny gradients. Dividing by sqrt(d_k) restores unit variance.",
            ),
            mcq(
                "q-tr-2",
                "KV Cache",
                "During autoregressive decoding, what is the main benefit of a Key-Value cache?",
                [
                    "It avoids recomputing K and V for prior tokens, reducing per-step attention work from O(N^2) to O(N)",
                    "It compresses embeddings by 50% using FP8 registers",
                    "It enables bidirectional attention during generation",
                    "It removes the need for positional information entirely",
                ],
                [0],
                "Without a cache every new token re-projects all previous tokens. Caching K and V means only the new token is projected each step.",
                qtype="Reasoning",
            ),
            mcq(
                "q-tr-3",
                "Rotary Position Embeddings",
                "How does RoPE encode position differently from absolute sinusoidal embeddings?",
                [
                    "It rotates Q and K in 2D planes so their inner product depends on relative distance (m - n)",
                    "It learns a lookup table added to token embeddings",
                    "It uses hyperbolic graph distance between tokens",
                    "It discards position and relies only on the causal mask",
                ],
                [0],
                "RoPE applies an orthogonal rotation, making the Q·K inner product a function of relative offset rather than absolute index.",
            ),
        ],
    },
    {
        "id": "assess-baseline-diagnostic",
        "title": "AI Engineer Baseline Diagnostic",
        "category": "Baseline Diagnostic",
        "skillId": "ml-supervised",
        "skillName": "General AI Foundations",
        "difficulty": "Beginner",
        "estimatedTime": "5 mins",
        "passingScore": 70,
        "description": "Establishes the starting point across statistics, regularisation and evaluation fundamentals.",
        "questions": [
            mcq(
                "q-diag-1",
                "Overfitting & Regularisation",
                "A model scores 99.2% on training data but 64.1% on the holdout. What is the most likely diagnosis?",
                [
                    "High variance (overfitting): the model memorised training noise",
                    "High bias (underfitting): the model is too simple",
                    "Target leakage from the validation split",
                    "The learning rate is too low to converge",
                ],
                [0],
                "A wide generalisation gap with strong training performance is the signature of high variance.",
            ),
            mcq(
                "q-diag-2",
                "Evaluation Metrics",
                "For a fraud detector where only 0.5% of transactions are fraudulent, which metric is most informative?",
                [
                    "Precision-Recall AUC",
                    "Accuracy",
                    "Mean squared error",
                    "R-squared",
                ],
                [0],
                "With extreme class imbalance, accuracy is dominated by the majority class. PR-AUC reflects performance on the rare positive class.",
            ),
            mcq(
                "q-diag-3",
                "Cross-Validation",
                "During hyperparameter search you standardise features using statistics of the whole dataset before splitting folds. What is the failure?",
                [
                    "Data leakage: validation folds influenced the preprocessing statistics",
                    "Underfitting caused by reduced feature variance",
                    "Nothing, standardisation is always safe before splitting",
                    "The model becomes non-deterministic across runs",
                ],
                [0],
                "Fitting scalers on the full dataset leaks validation information into training and inflates the reported score.",
            ),
        ],
    },
    {
        "id": "assess-rag-systems",
        "title": "Retrieval Augmented Generation & Hybrid Search",
        "category": "Skill Assessment",
        "skillId": "dl-rag-systems",
        "skillName": "Retrieval Augmented Generation (RAG)",
        "difficulty": "Advanced",
        "estimatedTime": "9 mins",
        "passingScore": 80,
        "description": "Covers chunking, hybrid retrieval, re-ranking latency budgets and groundedness evaluation.",
        "questions": [
            mcq(
                "q-rag-1",
                "Hybrid Retrieval",
                "Why combine BM25 lexical search with dense vector retrieval?",
                [
                    "Lexical search preserves exact identifiers and rare terms that dense embeddings can blur",
                    "BM25 is strictly more accurate than dense retrieval in every case",
                    "Dense retrieval cannot handle more than 10k documents",
                    "It removes the need for a re-ranking stage",
                ],
                [0],
                "Dense embeddings generalise semantics but smear rare tokens such as error codes, SKUs or function names. Hybrid fusion recovers exact-match recall.",
            ),
            mcq(
                "q-rag-2",
                "Re-ranking",
                "What is the trade-off of adding a cross-encoder re-ranker after vector recall?",
                [
                    "Better precision at the cost of extra latency because the model scores each candidate pair",
                    "Lower latency but much worse relevance",
                    "It removes the need for chunking",
                    "It guarantees removal of all hallucination",
                ],
                [0],
                "Cross-encoders jointly encode query and document, which is far more accurate but cannot be pre-computed, so it adds per-candidate cost.",
            ),
            mcq(
                "q-rag-3",
                "Groundedness Evaluation",
                "Which measurement best detects unsupported generation in a RAG system?",
                [
                    "Faithfulness / groundedness scoring of claims against retrieved context",
                    "BLEU against a reference dataset",
                    "Embedding dimension count",
                    "Number of documents indexed",
                ],
                [0],
                "Faithfulness metrics check whether every claim is entailed by retrieved context, which is what separates grounded answers from hallucination.",
            ),
        ],
    },
    {
        "id": "assess-vector-databases",
        "title": "Vector Indexing & ANN Trade-offs",
        "category": "Skill Assessment",
        "skillId": "data-vector-databases",
        "skillName": "Vector DBs & Embeddings Index",
        "difficulty": "Advanced",
        "estimatedTime": "7 mins",
        "passingScore": 80,
        "description": "Index families, recall/latency trade-offs and metric selection.",
        "questions": [
            mcq(
                "q-vdb-1",
                "ANN Index Families",
                "Which statement best describes HNSW relative to IVF-PQ?",
                [
                    "HNSW offers higher recall and lower query latency with a larger memory footprint",
                    "HNSW compresses vectors more aggressively than product quantisation",
                    "HNSW requires a training pass over the corpus before inserts",
                    "HNSW only supports exact nearest-neighbour search",
                ],
                [0],
                "HNSW builds a navigable small-world graph at query-time cost O(log N), trading memory for recall and speed; IVF-PQ compresses heavily after a training step.",
            ),
            mcq(
                "q-vdb-2",
                "Distance Metrics",
                "When are cosine similarity and inner product equivalent for ranking?",
                [
                    "When all vectors are L2-normalised",
                    "Always, they are identical metrics",
                    "Only when vectors have zero mean",
                    "Only for binary embeddings",
                ],
                [0],
                "With unit-norm vectors, cosine similarity equals the inner product, so an inner-product index becomes valid.",
            ),
        ],
    },
]


ASSESSMENT_INDEX: dict[str, dict[str, Any]] = {item["id"]: item for item in ASSESSMENTS}

# Foundational diagnostic item bank: real answer keys, no generated scores.
for aid, sid, name, questions in [
 ('assess-python-baseline','prog-python-advanced','Python (Advanced)',[
  mcq('py-list','Mutability','Which built-in Python collection is mutable?', ['tuple','list','str','frozenset'],[1],'Lists support in-place updates.'),
  mcq('py-set','Collections','Which collections keep unique values?', ['set','list','frozenset','tuple'],[0,2],'Sets and frozensets contain unique elements.','Multiple Select'),
  {'id':'py-keyword','type':'Short Answer','topic':'Functions','question':'Which keyword defines a function in Python?','correctAnswers':'def','explanation':'def introduces a function definition.'}
 ]),
 ('assess-sql-baseline','data-sql-querying','Advanced SQL & Data Modeling',[
  mcq('sql-filter','Filtering','Which clause filters rows before grouping?', ['HAVING','ORDER BY','WHERE','LIMIT'],[2],'WHERE filters input rows before GROUP BY.'),
  mcq('sql-left','Joins','Which join retains every row from the left table?', ['INNER JOIN','LEFT JOIN','CROSS JOIN','RIGHT JOIN'],[1],'LEFT JOIN preserves unmatched left-side rows.'),
  {'id':'sql-count','type':'Short Answer','topic':'Aggregation','question':'Name the SQL aggregate function that counts rows.','correctAnswers':'count','explanation':'COUNT aggregates row counts.'}
 ])]:
 ASSESSMENTS.append({'id':aid,'title':name+' Baseline Diagnostic','category':'Baseline Diagnostic','skillId':sid,'skillName':name,'difficulty':'Beginner','estimatedTime':'5 mins','questionsCount':len(questions),'questions':questions,'targetSkillsImpacted':[{'skillId':sid,'skillName':name,'baselineMastery':0,'targetMastery':80}]})

# Additional catalog-owned banks; advanced items test reasoning without executing code.
def add_bank(ident, skill_id, name, difficulty, questions):
    ASSESSMENTS.append({'id':ident,'title':name+' '+difficulty+' Assessment','description':'Scored knowledge and reasoning questions; no code execution.','category':'Skill Assessment','skillId':skill_id,'skillName':name,'difficulty':difficulty,'estimatedTime':'6 mins','passingScore':80,'questionsCount':len(questions),'questions':questions,'targetSkillsImpacted':[{'skillId':skill_id,'skillName':name,'baselineMastery':0,'targetMastery':80}]})

add_bank('assess-python-advanced','prog-python-advanced','Python (Advanced)','Advanced',[
 mcq('py-default','Function defaults','A function appends to a list parameter defined as items=[]. Why can separate calls share accumulated values?',['Default expressions are evaluated once when the function is defined','Python copies defaults after every call','Lists are immutable','The garbage collector resets arguments'],[0],'The default list is shared; use None and allocate a new list inside the function.'),
 mcq('py-generator','Iteration','What happens when a generator that has been fully consumed is iterated again?',['It restarts from the first yield','It produces no further values','It recreates the input list','It always raises TypeError'],[1],'A consumed generator is exhausted; create a new generator to repeat the sequence.'),
 mcq('py-closure','Closures','Functions created in a loop all refer to the same loop variable. Why might calling them later return the final loop value?',['Closures normally look up that variable when called','Functions cannot be created in loops','Each closure automatically copies every value','Loop variables are randomly assigned'],[0],'Late binding observes the current value; binding a default argument can capture each iteration value.')
])
add_bank('assess-sql-advanced','data-sql-querying','Advanced SQL & Data Modeling','Advanced',[
 mcq('sql-null','NULL semantics','In SQL, why does WHERE value = NULL not select rows whose value is NULL?',['Equality with NULL evaluates to unknown; use IS NULL','NULL is the empty string','NULL is zero','WHERE ignores comparisons'],[0],'SQL uses three-valued logic; IS NULL explicitly tests nullness.'),
 mcq('sql-window','Window functions','Which operation can attach a department average to each employee row while retaining every employee row?',['AVG(salary) OVER (PARTITION BY department)','GROUP BY department without a window','SELECT DISTINCT department','DELETE duplicate departments'],[0],'Window aggregates retain input row granularity.'),
 mcq('sql-outer-filter','Outer joins','After A LEFT JOIN B ON A.id=B.a_id, what does WHERE B.status = \'active\' do to unmatched A rows?',['Filters them out because the predicate is unknown for NULL','Always preserves them','Converts their B values to active','Duplicates them'],[0],'Move an appropriate right-table filter into ON if unmatched left rows must remain.')
])
add_bank('assess-html-baseline','web-html-css','HTML & CSS','Beginner',[
 mcq('html-button','Semantics','Which element is the appropriate default for an action that submits a form?',['button','span','div','h1'],[0],'A button supplies native keyboard and form semantics.'),
 mcq('html-label','Forms','How does an HTML label explicitly associate with an input?',['Its for attribute matches the input id','Its class matches the input value','Its text equals the placeholder','It appears anywhere in the page'],[0],'The for/id association gives the control an accessible label.'),
 mcq('css-responsive','Responsive layout','Which CSS feature applies rules depending on viewport conditions?',['A media query','An HTML comment','A database index','A cookie'],[0],'Media queries condition CSS rules on characteristics such as viewport width.')
])
add_bank('assess-networking-baseline','cloud-networking','Networking Fundamentals','Beginner',[
 mcq('net-dns','DNS','What is a common purpose of DNS?',['Resolve a domain name to an IP address','Encrypt every disk file','Compile JavaScript','Allocate CPU threads'],[0],'DNS resolves names through distributed resource records.'),
 mcq('net-tls','TLS','What does successful TLS provide when the peer certificate is properly validated?',['Encryption in transit and peer authentication','Proof that all application input is safe','Unlimited bandwidth','Automatic database backups'],[0],'TLS protects the connection; application security remains separate.'),
 mcq('net-tcp','TCP','Which property is associated with TCP?',['An ordered reliable byte stream','Mandatory preservation of message boundaries','No retransmission under any condition','Domain-name registration'],[0],'TCP provides an ordered byte stream; applications define message framing.')
])
add_bank('assess-linux-baseline','ops-linux','Linux Administration','Beginner',[
 mcq('linux-perms','Permissions','In rwxr-x---, what permissions does the group have?',['Read and execute','Read and write','All permissions','No permissions'],[0],'The middle three bits r-x apply to the group.'),
 mcq('linux-process','Processes','What does a process ID identify?',['A running process within its PID namespace','A permanent filename','A network password','A CPU manufacturer'],[0],'A PID identifies a process within its namespace and can later be reused.'),
 mcq('linux-pipe','Pipelines','What does the shell pipe operator normally connect?',['One command standard output to another command standard input','Two physical disks','A file to its owner','The terminal to every network interface'],[0],'Pipes let commands stream data between stdout and stdin.')
])
add_bank('assess-docker-baseline','prog-docker-containers','Docker & Containerization','Beginner',[
 mcq('docker-image','Images and containers','Which description distinguishes an image from a container?',['An image is a template; a container is a runtime instance','An image is always a running process','Containers cannot use images','They always mean the same thing'],[0],'Containers instantiate images with runtime configuration and a writable layer.'),
 mcq('docker-data','Persistence','Where should data that must survive container replacement typically be stored?',['A persistent volume or intentionally managed external store','Only in the container writable layer','Only in process memory','In the image tag text'],[0],'Persistent storage is managed independently of a replaceable container.'),
 mcq('docker-secret','Secrets','Why should a secret not be baked into a container image?',['Image layers and registries can retain and expose it','Images cannot store strings','Secrets disable DNS','It automatically encrypts all logs'],[0],'Supply secrets through a controlled runtime mechanism rather than image contents.')
])
for assessment in ASSESSMENTS:
    assessment.setdefault('passingScore',80)
ASSESSMENT_INDEX = {item['id']:item for item in ASSESSMENTS}
