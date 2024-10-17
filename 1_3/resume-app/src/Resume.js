// src/Resume.js
import React from 'react';

const Resume = () => {
  return (
    <div className="bg-gray-100 text-black font-sans">
      <div className="max-w-4xl mx-auto p-8 bg-white shadow-lg mt-10">
        {/* Header */}
        <div className="flex justify-between items-center border-b pb-4 mb-6">
          <div>
            <h1 className="text-4xl font-bold">[Your Name]</h1>
            <p className="text-lg text-gray-600">[Your Contact Information]</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">[City, State]</p>
          </div>
        </div>

        {/* Skills Section */}
        <section className="mb-8">
          <h2 className="text-2xl font-semibold border-b pb-2 mb-4">Skills</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>Programming Languages: Python, Java, JavaScript, SQL</li>
            <li>Web Development: HTML, CSS, JavaScript, React.js, Node.js</li>
            <li>Databases: MySQL, PostgreSQL, MongoDB</li>
            <li>Version Control: Git, GitHub</li>
            <li>Agile Methodologies: Scrum, Kanban</li>
            <li>Testing: Unit Testing, Integration Testing, Test Automation (Selenium)</li>
            <li>Cloud Services: AWS, Azure</li>
            <li>DevOps: CI/CD, Docker, Jenkins</li>
          </ul>
        </section>

        {/* Education Section */}
        <section className="mb-8">
          <h2 className="text-2xl font-semibold border-b pb-2 mb-4">Education</h2>
          <div className="mb-6">
            <p className="text-lg font-bold">M.S. Technology Systems Management</p>
            <p className="text-sm text-gray-600">[University Name], Aug 2022 - Dec 2023</p>
            <p className="text-sm text-gray-600">Relevant Courses: Software Engineering, Database Systems, Cloud Computing</p>
            <p className="text-sm text-gray-600">CAA Academic Honor Roll, Scholarship-Athlete, Leadership role in SBU Football Team</p>
          </div>
          <div>
            <p className="text-lg font-bold">B.S. Multidisciplinary Studies with Focus in IT</p>
            <p className="text-sm text-gray-600">[University Name], Jun 2018 - May 2022</p>
            <p className="text-sm text-gray-600">Relevant Courses: Computer Science Fundamentals, Data Structures, Web Development</p>
          </div>
        </section>

        {/* Work Experience Section */}
        <section className="mb-8">
          <h2 className="text-2xl font-semibold border-b pb-2 mb-4">Work Experience</h2>
          {/* Add your work experience here */}
        </section>

        {/* Projects Section */}
        <section className="mb-8">
          <h2 className="text-2xl font-semibold border-b pb-2 mb-4">Projects</h2>
          <ul className="list-disc pl-5 space-y-2 text-sm text-gray-700">
            <li><strong>[Project Name]</strong>: Project details here.</li>
          </ul>
        </section>

        {/* Certifications Section */}
        <section>
          <h2 className="text-2xl font-semibold border-b pb-2 mb-4">Certifications</h2>
          <ul className="list-disc pl-5 space-y-1 text-sm text-gray-700">
            <li>AWS Certified Developer – Associate</li>
            <li>Certified Scrum Developer (CSD)</li>
            <li>Microsoft Certified: Azure Developer Associate</li>
          </ul>
        </section>
      </div>

      {/* Print Button */}
      <div className="flex justify-center mt-8 no-print">
        <button onClick={() => window.print()} className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
          Print / Save as PDF
        </button>
      </div>
    </div>
  );
};

export default Resume;
