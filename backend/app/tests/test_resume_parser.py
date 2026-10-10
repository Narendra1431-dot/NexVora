from app.services.resume_parser import extract_sections

def test_section_headings_preserve_text_without_fabricating_sections():
    sections=extract_sections('QA Learner\nSkills: Python, SQL\nEducation\nComputer Science\nExperience\nBuilt a class project')
    assert [s['name'] for s in sections]==['unclassified','skills','education','experience']
    assert sections[1]['text']=='Python, SQL'
    assert sections[-1]['text']=='Built a class project'
    assert extract_sections('I gained experience and skills through projects.')==[{'name':'unclassified','text':'I gained experience and skills through projects.'}]
    assert extract_sections('')==[]
