import React from 'react';

export default function TrainingPlanCards({ recommendations }) {
  const getPriorityStyle = (priority) => {
    if (priority === 'Critical') {
      return 'text-red-700 border-red-300 bg-white';
    }
    if (priority === 'Important') {
      return 'text-orange-700 border-orange-300 bg-white';
    }
    return 'text-blue-700 border-blue-300 bg-white';
  };

  return (
    <div className="grid md:grid-cols-2 gap-4">
      {recommendations.map((rec) => (
        <div
          key={rec.id}
          className="border border-gray-200 rounded-md shadow-sm p-4 bg-white hover:shadow-md transition-shadow"
        >
          {/* Header */}
          <div className="flex justify-between items-start mb-3">
            <h3 className="text-sm font-semibold text-gray-900 flex-1 pr-3">
              {rec.recommendedCourse.title}
            </h3>
            <span className="px-2 py-1 text-xs rounded-md border bg-white text-green-700 font-medium border-green-300 whitespace-nowrap">
              {rec.matchScore}% Match
            </span>
          </div>

          {/* Details */}
          <p className="text-xs text-gray-600 mb-2">
            <span className="font-medium">Addressed Qualification:</span> {rec.qualificationName}
          </p>

          <p className="text-xs text-gray-600 mb-3">
            <span className="font-medium">Skills:</span> {rec.requiredSkills.join(', ')}
          </p>

          {/* Meta Info */}
          <div className="text-xs text-gray-500 flex gap-4 mb-4">
            <span>{rec.recommendedCourse.durationHours}h · {rec.recommendedCourse.format}</span>
            <span className="text-blue-600 font-medium">
              {rec.applicableEmployees.length} employees need this
            </span>
          </div>

          {/* Priority Badge */}
          {rec.priority && (
            <div className="mb-4">
              <span className={`px-2 py-1 rounded-md border text-xs font-normal ${getPriorityStyle(rec.priority)}`}>
                Priority: {rec.priority}
              </span>
            </div>
          )}

          {/* CTA */}
          <div className="flex justify-end border-t border-gray-100 pt-3">
            <button className="px-4 py-2 text-sm bg-[#4CAF50] text-white rounded-md hover:bg-[#388E3C] transition-colors font-normal">
              Assign to Selected
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
