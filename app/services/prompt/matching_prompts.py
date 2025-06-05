"""
Prompts for AI-powered job matching using Gemini API
"""


class MatchingPrompts:
    """Collection of prompts for job matching analysis"""

    @staticmethod
    def get_cv_job_compatibility_prompt(cv_text: str, job_title: str, job_description: str) -> str:
        """
        Generate prompt for CV-Job compatibility analysis

        Args:
            cv_text: Candidate's CV content (limited to 3000 chars)
            job_title: Job offer title
            job_description: Job offer description (limited to 2000 chars)

        Returns:
            Formatted prompt for Gemini API
        """

        # Limit text lengths to avoid token limits
        cv_text_limited = cv_text[:3000] if cv_text else ""
        job_description_limited = job_description[:2000] if job_description else ""

        return f"""
Analyze the compatibility between this CV and job offer. Provide a detailed analysis in JSON format.

CV Content:
{cv_text_limited}

Job Title: {job_title}
Job Description: {job_description_limited}

Please analyze and return ONLY a valid JSON object with this exact structure:
{{
    "compatibility_score": <integer between 0 and 100>,
    "matched_skills": [<list of matching skills/technologies found in both>],
    "missing_skills": [<list of important skills from job that are missing in CV>],
    "analysis_summary": "<brief explanation of the match quality>",
    "strengths": [<list of candidate's strengths for this role>],
    "recommendations": [<list of improvements or skills to develop>]
}}

Analysis Criteria:
1. Technical skills alignment (40% weight)
   - Programming languages, frameworks, tools
   - Technology stack compatibility
   - Technical expertise level match

2. Experience level match (25% weight)
   - Years of experience alignment
   - Seniority level compatibility
   - Project complexity match

3. Industry/domain relevance (20% weight)
   - Sector experience alignment
   - Domain knowledge compatibility
   - Business context understanding

4. Educational background fit (10% weight)
   - Degree requirements match
   - Certification alignment
   - Continuous learning evidence

5. Career progression alignment (5% weight)
   - Career path consistency
   - Growth trajectory match
   - Role transition logic

Scoring Guidelines:
- 90-100: Excellent match, highly qualified candidate
- 80-89: Very good match, strong candidate with minor gaps
- 70-79: Good match, qualified with some skill development needed
- 60-69: Moderate match, candidate needs significant development
- 50-59: Weak match, major gaps in requirements
- 0-49: Poor match, fundamental misalignment

Important Instructions:
- Be precise and analytical in your assessment
- Focus on concrete skills and experience evidence
- Prioritize quality over quantity in skill matching
- Consider transferable skills and learning potential
- Return only the JSON object, no additional text or formatting
- Ensure all array fields contain strings, not objects
- Limit matched_skills to top 10 most relevant
- Limit missing_skills to top 5 most critical gaps
- Limit strengths to top 5 most significant advantages
- Limit recommendations to top 3 most actionable items
"""

    @staticmethod
    def get_skill_extraction_prompt(text: str) -> str:
        """
        Generate prompt for extracting skills from text

        Args:
            text: Text to analyze for skills

        Returns:
            Formatted prompt for skill extraction
        """

        text_limited = text[:2000] if text else ""

        return f"""
Extract technical and professional skills from this text. Return a JSON array of skills.

Text to analyze:
{text_limited}

Return ONLY a JSON array in this format:
[
    "skill1",
    "skill2",
    "skill3"
]

Focus on:
- Programming languages (Python, Java, JavaScript, etc.)
- Frameworks and libraries (React, Django, Spring, etc.)
- Technologies and tools (Docker, AWS, Git, etc.)
- Methodologies (Agile, Scrum, DevOps, etc.)
- Database technologies (PostgreSQL, MongoDB, etc.)
- Professional skills (Project Management, Leadership, etc.)

Rules:
- Extract only concrete, identifiable skills
- Use standard naming conventions (e.g., "JavaScript" not "js")
- Avoid vague terms like "good communication"
- Limit to maximum 20 most relevant skills
- Return only the JSON array, no additional text
"""

    @staticmethod
    def get_job_requirements_prompt(job_title: str, job_description: str) -> str:
        """
        Generate prompt for extracting job requirements

        Args:
            job_title: Job offer title
            job_description: Job offer description

        Returns:
            Formatted prompt for requirements extraction
        """

        job_description_limited = job_description[:2000] if job_description else ""

        return f"""
Extract and categorize job requirements from this job posting. Return a structured JSON analysis.

Job Title: {job_title}
Job Description: {job_description_limited}

Return ONLY a JSON object with this structure:
{{
    "required_skills": [<list of mandatory technical skills>],
    "preferred_skills": [<list of nice-to-have skills>],
    "experience_level": "<junior/mid/senior/lead>",
    "minimum_years": <number or 0 if not specified>,
    "education_requirements": [<list of education/certification requirements>],
    "soft_skills": [<list of interpersonal/communication skills>],
    "responsibilities": [<list of main job responsibilities>],
    "industry_domain": "<primary industry/domain>"
}}

Guidelines:
- Distinguish between "must-have" and "nice-to-have" requirements
- Infer experience level from job title and requirements
- Extract concrete skills, not vague descriptions
- Limit each array to maximum 10 items
- Use standard skill naming conventions
- Return only the JSON object, no additional text
"""

    @staticmethod
    def get_career_advice_prompt(cv_text: str, target_role: str) -> str:
        """
        Generate prompt for career development advice

        Args:
            cv_text: Candidate's CV content
            target_role: Desired role or career direction

        Returns:
            Formatted prompt for career advice
        """

        cv_text_limited = cv_text[:2500] if cv_text else ""

        return f"""
Provide career development advice based on this CV and target role. Return structured guidance in JSON format.

Current CV:
{cv_text_limited}

Target Role: {target_role}

Return ONLY a JSON object with this structure:
{{
    "current_strengths": [<list of candidate's main strengths>],
    "skill_gaps": [<list of skills to develop for target role>],
    "learning_path": [<ordered list of learning recommendations>],
    "experience_recommendations": [<list of experience to gain>],
    "certification_suggestions": [<list of relevant certifications>],
    "timeline_estimate": "<realistic timeframe to reach target role>",
    "next_steps": [<list of immediate actionable steps>]
}}

Focus on:
- Realistic and actionable advice
- Specific skills and technologies to learn
- Practical ways to gain relevant experience
- Industry-standard certifications
- Clear progression pathway
- Immediate next steps candidate can take

Return only the JSON object, no additional formatting or text.
"""