// Classification statistics widget for dashboard
import React from 'react';
import { getCategoryColor, getCategoryLabel } from '@/utils/emailUtils';

interface ClassificationStatsProps {
  emailsByCategory: Record<string, number>;
  totalEmails: number;
  classifyingCount: number;
}

export const ClassificationStats: React.FC<ClassificationStatsProps> = ({
  emailsByCategory,
  totalEmails,
  classifyingCount,
}) => {
  const containerStyle = {
    backgroundColor: '#fff',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    padding: '24px',
    height: '100%',
  };

  const titleStyle = {
    margin: '0 0 16px 0',
    fontSize: '18px',
    fontWeight: '600',
    color: '#333',
  };

  const statsContainerStyle = {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
  };

  const statRowStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '8px 12px',
    backgroundColor: '#f8f9fa',
    borderRadius: '6px',
    transition: 'all 0.2s ease',
  };

  const categoryLabelStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
    fontWeight: '500',
  };

  const countStyle = {
    fontSize: '16px',
    fontWeight: '700',
    color: '#333',
  };

  const progressContainerStyle = {
    marginTop: '16px',
    paddingTop: '16px',
    borderTop: '1px solid #e0e0e0',
  };

  const progressLabelStyle = {
    fontSize: '12px',
    color: '#6c757d',
    marginBottom: '8px',
  };

  const progressBarStyle = {
    height: '8px',
    backgroundColor: '#e9ecef',
    borderRadius: '4px',
    overflow: 'hidden',
  };

  const progressFillStyle = (percentage: number) => ({
    height: '100%',
    width: `${percentage}%`,
    backgroundColor: '#007acc',
    transition: 'width 0.3s ease',
  });

  const classifiedCount = totalEmails - classifyingCount;
  const classificationProgress = totalEmails > 0 ? (classifiedCount / totalEmails) * 100 : 0;

  // Sort categories by count
  const sortedCategories = Object.entries(emailsByCategory)
    .filter(([_, count]) => count > 0)
    .sort(([, a], [, b]) => b - a);

  return (
    <div style={containerStyle}>
      <h3 style={titleStyle}>📊 Email Classification</h3>

      {classifyingCount > 0 && (
        <div style={progressContainerStyle}>
          <div style={progressLabelStyle}>
            Classifying {classifyingCount} of {totalEmails} emails... ({Math.round(classificationProgress)}% complete)
          </div>
          <div style={progressBarStyle}>
            <div style={progressFillStyle(classificationProgress)} />
          </div>
        </div>
      )}

      <div style={statsContainerStyle}>
        {sortedCategories.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '24px', color: '#6c757d' }}>
            <div style={{ fontSize: '48px', marginBottom: '8px' }}>🤖</div>
            <div>No classified emails yet</div>
            <div style={{ fontSize: '12px', marginTop: '4px' }}>
              {classifyingCount > 0 ? 'Classification in progress...' : 'Load emails to see classifications'}
            </div>
          </div>
        ) : (
          sortedCategories.map(([category, count]) => {
            const percentage = ((count / totalEmails) * 100).toFixed(1);
            return (
              <div
                key={category}
                style={statRowStyle}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateX(4px)';
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateX(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div style={categoryLabelStyle}>
                  <div
                    style={{
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      backgroundColor: getCategoryColor(category),
                    }}
                  />
                  <span>{getCategoryLabel(category)}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '12px', color: '#6c757d' }}>
                    {percentage}%
                  </span>
                  <span style={countStyle}>{count}</span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {sortedCategories.length > 0 && (
        <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #e0e0e0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px' }}>
            <span style={{ fontWeight: '600' }}>Total Classified:</span>
            <span style={{ fontWeight: '700', color: '#007acc' }}>{classifiedCount} / {totalEmails}</span>
          </div>
        </div>
      )}
    </div>
  );
};
