"""Topic bibliography and discovery terms; careers are resolved from MongoDB."""
def books(*pairs): return [{'title':t,'author':a} for t,a in pairs]
MATH=books(('Introduction to Linear Algebra','Gilbert Strang'),('Numerical Linear Algebra','Lloyd N. Trefethen and David Bau III'))
CALCULUS=books(('Vector Calculus','Jerrold E. Marsden and Anthony J. Tromba'),('Calculus','Michael Spivak'))
STATS=books(('Introduction to Probability','Joseph K. Blitzstein and Jessica Hwang'),('All of Statistics','Larry Wasserman'))
OPT=books(('Convex Optimization','Stephen Boyd and Lieven Vandenberghe'),('Numerical Optimization','Jorge Nocedal and Stephen J. Wright'))
PYTHON=books(('Fluent Python','Luciano Ramalho'),('Effective Python','Brett Slatkin'))
DSA=books(('Introduction to Algorithms','Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest and Clifford Stein'),('Algorithm Design','Jon Kleinberg and Eva Tardos'))
DATA=books(('Python for Data Analysis','Wes McKinney'),('Python Data Science Handbook','Jake VanderPlas'))
SQL=books(('Learning SQL','Alan Beaulieu'),('SQL Performance Explained','Markus Winand'))
ML=books(('Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow','Aurelien Geron'),('Pattern Recognition and Machine Learning','Christopher M. Bishop'),('The Elements of Statistical Learning','Trevor Hastie, Robert Tibshirani and Jerome Friedman'))
DL=books(('Deep Learning','Ian Goodfellow, Yoshua Bengio and Aaron Courville'),('Dive into Deep Learning','Aston Zhang, Zachary C. Lipton, Mu Li and Alexander J. Smola'))
NLP=books(('Natural Language Processing with Transformers','Lewis Tunstall, Leandro von Werra and Thomas Wolf'),('Build a Large Language Model (From Scratch)','Sebastian Raschka'))
MLOPS=books(('Designing Machine Learning Systems','Chip Huyen'),('Practical MLOps','Noah Gift and Alfredo Deza'))
SYSTEMS=books(('Designing Data-Intensive Applications','Martin Kleppmann'),('Fundamentals of Data Engineering','Joe Reis and Matt Housley'))
DOCKER=books(('Docker Deep Dive','Nigel Poulton'),('Docker: Up & Running','Sean P. Kane and Karl Matthias'))
TEST=books(('Python Testing with pytest','Brian Okken'),('Continuous Delivery','Jez Humble and David Farley'))
API=books(('API Design Patterns','JJ Geewax'),('Designing Web APIs','Brenda Jin, Saurabh Sahni and Amir Shevat'))
WEB=books(('HTML and CSS: Design and Build Websites','Jon Duckett'),('Learning Web Design','Jennifer Niederst Robbins'))
JS=books(('Effective TypeScript','Dan Vanderkam'),('JavaScript: The Definitive Guide','David Flanagan'))
REACT=books(('Learning React','Alex Banks and Eve Porcello'),('The Road to React','Robin Wieruch'))
NET=books(('Computer Networking: A Top-Down Approach','James F. Kurose and Keith W. Ross'),('Computer Networks','Andrew S. Tanenbaum and David J. Wetherall'))
SEC=books(('Threat Modeling: Designing for Security','Adam Shostack'),('Web Application Security','Andrew Hoffman'))
LINUX=books(('The Linux Command Line','William Shotts'),('How Linux Works','Brian Ward'))
IAC=books(('Terraform: Up & Running','Yevgeniy Brikman'),('Infrastructure as Code','Kief Morris'))

# id: search query, exact-topic title aliases, books, primary reference
TOPICS = {
'math-linear-algebra':('linear algebra 3Blue1Brown',['linear','matri','vector','eigen'],MATH,'https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/'),
'math-multivariate-calculus':('multivariable calculus gradient Khan Academy',['gradient','multivariable','partial derivative','chain rule'],CALCULUS,'https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/'),
'math-prob-stats':('statistics fundamentals StatQuest',['statistic','probability','variance','bayes'],STATS,'https://seeing-theory.brown.edu/'),
'math-optimization':('gradient descent Adam optimization StatQuest',['gradient','optim','adam'],OPT,'https://web.stanford.edu/~boyd/cvxbook/'),
'prog-python-advanced':('python course freeCodeCamp',['python'],PYTHON,'https://docs.python.org/3/tutorial/'),
'prog-data-structures':('data structures algorithms python freeCodeCamp',['data structures','algorithm'],DSA,'https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/'),
'prog-docker-containers':('docker tutorial TechWorld with Nana',['docker','container'],DOCKER,'https://docs.docker.com/get-started/'),
'prog-testing-cicd':('pytest github actions tutorial freeCodeCamp',['pytest','testing','ci/cd','github actions'],TEST,'https://docs.pytest.org/en/stable/'),
'prog-rest-apis':('api development FastAPI python freeCodeCamp',['api','fastapi'],API,'https://fastapi.tiangolo.com/tutorial/'),
'data-numpy-pandas':('pandas numpy python freeCodeCamp',['pandas','numpy'],DATA,'https://pandas.pydata.org/docs/user_guide/index.html'),
'data-sql-querying':('SQL database course freeCodeCamp',['sql','database'],SQL,'https://www.postgresql.org/docs/current/tutorial.html'),
'data-vector-databases':('vector databases embeddings IBM Technology',['vector','embedding'],SYSTEMS,'https://www.ibm.com/think/topics/vector-database'),
'data-feature-store':('feature store Databricks',['feature store','version','dvc'],SYSTEMS,'https://docs.feast.dev/'),
'ml-supervised':('machine learning supervised freeCodeCamp',['machine learning','supervised','regression','xgboost'],ML,'https://scikit-learn.org/stable/supervised_learning.html'),
'ml-unsupervised':('PCA clustering StatQuest',['pca','clustering','k-means','unsupervised'],ML,'https://scikit-learn.org/stable/unsupervised_learning.html'),
'ml-model-evaluation':('cross validation ROC AUC StatQuest',['validation','roc','auc','precision','recall'],ML,'https://scikit-learn.org/stable/modules/model_evaluation.html'),
'ml-experiment-tracking':('MLflow experiment tracking tutorial',['mlflow','experiment tracking','weights'],MLOPS,'https://mlflow.org/docs/latest/ml/'),
'dl-neural-networks':('neural networks 3Blue1Brown',['neural','backprop'],DL,'https://www.deeplearningbook.org/'),
'dl-pytorch':('PyTorch deep learning full course freeCodeCamp',['pytorch'],DL,'https://docs.pytorch.org/tutorials/beginner/basics/intro.html'),
'dl-transformers':('transformers attention 3Blue1Brown',['transformer','attention'],NLP,'https://huggingface.co/learn/llm-course/chapter1/1'),
'dl-rag-systems':('retrieval augmented generation RAG IBM Technology',['retrieval','rag'],NLP,'https://www.ibm.com/think/topics/retrieval-augmented-generation'),
'dl-llm-finetuning':('fine tuning LoRA quantization IBM Technology',['fine-tun','fine tun','lora','quantiz'],NLP,'https://huggingface.co/docs/peft/index'),
'dl-prompt-engineering':('prompt engineering course freeCodeCamp',['prompt','context engineering'],NLP,'https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents'),
'dl-computer-vision':('computer vision course freeCodeCamp',['computer vision','convolution','cnn','opencv'],DL,'https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial.html'),
'mlops-model-serving':('LLM inference serving vLLM IBM Technology',['inference','serving','vllm','deploy'],MLOPS,'https://docs.vllm.ai/en/latest/'),
'mlops-production-pipeline':('MLOps course production pipelines freeCodeCamp',['mlops','pipeline','production'],MLOPS,'https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning'),
'mlops-monitoring':('ML model monitoring data drift Evidently',['drift','model monitoring','ml monitoring'],MLOPS,'https://www.evidentlyai.com/ml-in-production/data-drift'),
'web-html-css':('HTML CSS course freeCodeCamp',['html','css'],WEB,'https://developer.mozilla.org/en-US/docs/Learn_web_development'),
'web-typescript':('TypeScript course freeCodeCamp',['typescript','javascript'],JS,'https://www.typescriptlang.org/docs/handbook/intro.html'),
'web-react':('React course freeCodeCamp',['react'],REACT,'https://react.dev/learn'),
'cloud-networking':('networking fundamentals freeCodeCamp',['network','dns','tcp','tls'],NET,'https://cloud.google.com/learn/what-is-a-computer-network'),
'security-threats':('threat modeling OWASP application security IBM Technology',['threat','security','owasp'],SEC,'https://owasp.org/www-community/Threat_Modeling'),
'ops-linux':('Linux course freeCodeCamp',['linux'],LINUX,'https://www.kernel.org/doc/html/latest/admin-guide/'),
'ops-iac':('Terraform infrastructure as code TechWorld with Nana',['terraform','infrastructure as code'],IAC,'https://developer.hashicorp.com/terraform/tutorials'),
}

