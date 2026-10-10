"""Official provider catalog, links checked 2026-09-30. No third-party logo assets."""

def item(id, name, provider, initials, categories, level, description, url):
    return dict(id=id, name=name, provider=provider, initials=initials, categories=categories,
                level=level, description=description, officialUrl=url, linkCheckedAt='2026-09-30')

CATALOG = [
    item('aws-developer', 'AWS Certified Developer - Associate', 'Amazon Web Services', 'AWS', ['Cloud','Development'], 'Associate', 'Develop, deploy and troubleshoot applications on AWS.', 'https://aws.amazon.com/certification/certified-developer-associate/'),
    item('google-cloud-engineer', 'Google Cloud Associate Cloud Engineer', 'Google Cloud', 'GC', ['Cloud'], 'Associate', 'Deploy applications and manage cloud infrastructure and access.', 'https://cloud.google.com/learn/certification/cloud-engineer'),
    item('azure-ai-developer', 'Microsoft Azure AI Cloud Developer Associate', 'Microsoft', 'MS', ['AI/ML','Cloud','Development'], 'Associate', 'Implement AI solutions and back-end services on Azure.', 'https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-cloud-developer-associate/'),
    item('terraform-associate', 'HashiCorp Terraform Associate', 'HashiCorp', 'HC', ['DevOps','Cloud'], 'Associate', 'Validate foundational infrastructure-as-code skills with Terraform.', 'https://developer.hashicorp.com/certifications'),
    item('ckad', 'Linux Foundation CKAD', 'Linux Foundation / CNCF', 'LF', ['DevOps','Cloud'], 'Intermediate', 'Design, build and deploy cloud-native applications for Kubernetes.', 'https://training.linuxfoundation.org/certification/certified-kubernetes-application-developer-ckad/'),
    item('github-foundations', 'GitHub Foundations Certification', 'GitHub', 'GH', ['Development','DevOps'], 'Beginner', 'Git, repositories, collaboration and modern development practices.', 'https://learn.microsoft.com/en-us/credentials/certifications/github-foundations/'),
    item('mongodb-developer', 'MongoDB Associate Developer Certification', 'MongoDB', 'MDB', ['Database','Development'], 'Associate', 'Validate application development skills using MongoDB. Select your programming language on the official page.', 'https://learn.mongodb.com/pages/mongodb-associate-developer-exam'),
    item('fcc-javascript', 'freeCodeCamp JavaScript Certification', 'freeCodeCamp', 'fCC', ['Development'], None, 'Learn JavaScript through lessons, projects and a certification exam.', 'https://www.freecodecamp.org/learn/javascript-v9'),
    item('fcc-web-design', 'freeCodeCamp Responsive Web Design', 'freeCodeCamp', 'fCC', ['Development'], None, 'Build responsive websites with HTML and CSS through practical projects.', 'https://www.freecodecamp.org/learn/responsive-web-design-v9'),
    item('fcc-python', 'freeCodeCamp Python', 'freeCodeCamp', 'fCC', ['Development'], None, 'Practice Python programming, data structures and algorithms.', 'https://www.freecodecamp.org/learn/python-v9'),
    item('fcc-databases', 'freeCodeCamp Relational Databases', 'freeCodeCamp', 'fCC', ['Database'], None, 'Develop relational database and SQL skills through hands-on coursework.', 'https://www.freecodecamp.org/learn/relational-databases-v9'),
    item('cisco-exams', 'Cisco Certification Exams', 'Cisco', 'CS', ['Networking'], 'Multiple levels', 'Explore Cisco certification exams. This is a certification family; identify your specific award in the credential ID or URL.', 'https://www.cisco.com/site/us/en/learn/training-certifications/exams/index.html'),
    item('redhat-rhcsa', 'Red Hat RHCSA', 'Red Hat', 'RH', ['Linux'], None, 'Demonstrate core Red Hat Enterprise Linux system administration skills.', 'https://www.redhat.com/en/services/certification/rhcsa'),
]
BY_ID = {c['id']: c for c in CATALOG}
