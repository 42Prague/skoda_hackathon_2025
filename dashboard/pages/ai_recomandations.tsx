import { useState, useEffect } from 'react';
import { Clock, Award, BookOpen, ChevronDown, ChevronUp } from 'lucide-react';
import { AI_RECOMMENDATIONS } from '../components/data/mockData';

export default function AIRecommendations() {
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    const storedUser = localStorage.getItem('archerUser');
    if (storedUser) {
      setCurrentUser(JSON.parse(storedUser));
    }
  }, []);

  if (!currentUser) {
    return <div>Loading...</div>;
  }

  const recommendations = currentUser.role === 'Worker'
    ? AI_RECOMMENDATIONS.filter(rec => rec.applicableEmployees.includes(currentUser.id))
    : AI_RECOMMENDATIONS;

  const getPriorityStyle = (priority: string) => {
    const styles: Record<string, string> = {
      Critical: 'text-red-700 border-red-300 bg-white',
      Important: 'text-orange-700 border-orange-300 bg-white',
      Optional: 'text-blue-700 border-blue-300 bg-white'
    };
    return styles[priority] || 'text-gray-700 border-gray-300 bg-white';
  };

  return (
    <div className="max-w-[1200px] mx-auto p-6 space-y-6">
      {/* Page Header */}
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-2xl font-semibold text-gray-900">AI-Suggested Training Programs</h1>
        <p className="text-sm text-gray-600 mt-1">
          {currentUser.role === 'Worker'
            ? 'Personalized course recommendations based on your skill gaps'
            : 'Smart training suggestions to address team qualification gaps'}
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-md p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <BookOpen className="w-5 h-5 text-[#1565C0]" strokeWidth={2} />
            <span className="text-sm text-gray-600">Recommendations</span>
          </div>
          <p className="text-3xl font-normal text-gray-900">{recommendations.length}</p>
          <p className="text-xs text-gray-500 mt-1">Courses suggested</p>
        </div>

        <div className="bg-white border border-gray-200 rounded-md p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <Award className="w-5 h-5 text-[#4CAF50]" strokeWidth={2} />
            <span className="text-sm text-gray-600">Qualifications</span>
          </div>
          <p className="text-3xl font-normal text-gray-900">{recommendations.length}</p>
          <p className="text-xs text-gray-500 mt-1">Skills covered</p>
        </div>

        <div className="bg-white border border-gray-200 rounded-md p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-5 h-5 text-[#FB8C00]" strokeWidth={2} />
            <span className="text-sm text-gray-600">Learning Time</span>
          </div>
          <p className="text-3xl font-normal text-gray-900">
            {recommendations.reduce((sum, rec) => sum + rec.recommendedCourse.durationHours, 0)}h
          </p>
          <p className="text-xs text-gray-500 mt-1">Total duration</p>
        </div>
      </div>

      {/* Training Recommendations */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <div className="border-b border-gray-200 pb-3 mb-4">
          <h2 className="text-lg font-medium text-gray-900">Recommended Courses</h2>
          <p className="text-sm text-gray-600 mt-1">AI-matched training based on skill gaps and role requirements</p>
        </div>

        <div className="space-y-3">
          {recommendations.map((rec) => (
            <div
              key={rec.id}
              className="border border-gray-200 rounded-md shadow-sm p-4 hover:shadow-md transition-shadow bg-white"
            >
              {/* Card Header */}
              <div className="flex justify-between items-start mb-3">
                <div className="flex-1 pr-3">
                  <h3 className="text-base font-semibold text-gray-900 mb-1">
                    {rec.recommendedCourse.title}
                  </h3>
                  <p className="text-xs text-gray-600">
                    {rec.recommendedCourse.provider} · {rec.recommendedCourse.durationHours}h · {rec.recommendedCourse.format}
                  </p>
                </div>
                <span className="px-2 py-1 text-xs rounded-md border bg-white text-green-700 font-medium border-green-300 whitespace-nowrap">
                  {rec.matchScore}% Match
                </span>
              </div>

              {/* Qualification Info */}
              <div className="mb-3">
                <p className="text-xs text-gray-600 mb-2">
                  <span className="font-medium text-gray-900">Addresses Qualification:</span> {rec.qualificationName}
                </p>
                <div className="flex flex-wrap gap-2">
                  {rec.requiredSkills.map(skill => (
                    <span key={skill} className="px-2 py-1 rounded-md border bg-gray-50 text-gray-700 text-xs font-normal">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Priority Badge */}
              <div className="mb-3">
                <span className={`px-2 py-1 rounded-md border text-xs font-normal ${getPriorityStyle(rec.priority)}`}>
                  Priority: {rec.priority}
                </span>
              </div>

              {/* Expandable Explanation */}
              <div className="border-t border-gray-100 pt-3 mb-3">
                <button
                  onClick={() => setExpandedId(expandedId === rec.id ? null : rec.id)}
                  className="flex items-center justify-between w-full text-left group"
                >
                  <span className="text-sm font-medium text-[#1565C0] group-hover:text-[#0D47A1]">
                    Why this course?
                  </span>
                  {expandedId === rec.id ? (
                    <ChevronUp size={16} className="text-gray-500" />
                  ) : (
                    <ChevronDown size={16} className="text-gray-500" />
                  )}
                </button>

                {expandedId === rec.id && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-md border border-gray-200">
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {rec.explanation}
                    </p>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-3 border-t border-gray-100 pt-3">
                {currentUser.role === 'Worker' ? (
                  <>
                    <button className="flex-1 px-4 py-2 text-sm bg-[#4CAF50] text-white rounded-md hover:bg-[#388E3C] transition-colors font-normal">
                      Start Learning
                    </button>
                    <button className="px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors font-normal">
                      View Details
                    </button>
                  </>
                ) : (
                  <>
                    <button className="flex-1 px-4 py-2 text-sm bg-[#4CAF50] text-white rounded-md hover:bg-[#388E3C] transition-colors font-normal">
                      Assign to Team ({rec.applicableEmployees.length})
                    </button>
                    <button className="px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors font-normal">
                      View Course
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
