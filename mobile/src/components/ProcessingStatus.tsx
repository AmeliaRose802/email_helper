/**
 * Processing Status Component
 * 
 * This component displays real-time processing status with progress tracking,
 * job details, and interactive controls for cancelling or retrying processing.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { useWebSocket } from '../hooks/useWebSocket';
import { 
  processingApi, 
  ProcessingStatusResponse, 
  JobStatusResponse, 
  ProcessingUtils 
} from '../services/processingApi';

interface ProcessingStatusProps {
  pipelineId: string;
  userId: string;
  onComplete?: (results: any) => void;
  onError?: (error: string) => void;
  onCancel?: () => void;
}

interface ProcessingUpdate {
  type: string;
  pipeline_id?: string;
  job_id?: string;
  status?: string;
  progress?: number;
  message?: string;
  error?: string;
  result?: any;
  timestamp: string;
}

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
  pipelineId,
  userId,
  onComplete,
  onError,
  onCancel,
}) => {
  const [pipeline, setPipeline] = useState<ProcessingStatusResponse | null>(null);
  const [jobs, setJobs] = useState<JobStatusResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // WebSocket connection for real-time updates
  const { 
    isConnected, 
    error: wsError, 
    sendMessage,
    subscribeToPipeline,
    cancelPipeline,
    retryFailedJobs,
  } = useWebSocket(
    processingApi.getWebSocketUrl(pipelineId, userId),
    {
      onMessage: handleWebSocketMessage,
      onConnect: () => {
        console.log('Connected to processing WebSocket');
        subscribeToPipeline(pipelineId);
      },
      onError: (error) => {
        console.error('WebSocket error:', error);
        setError('Real-time updates unavailable');
      },
    }
  );

  // Handle WebSocket messages
  function handleWebSocketMessage(message: ProcessingUpdate) {
    setLastUpdate(new Date());
    
    switch (message.type) {
      case 'pipeline_status':
        if (message.pipeline_id === pipelineId) {
          // Refresh pipeline status
          loadPipelineStatus();
        }
        break;
        
      case 'job_status':
        if (message.job_id) {
          // Update specific job status
          setJobs(prevJobs => 
            prevJobs.map(job => 
              job.job_id === message.job_id 
                ? { 
                    ...job, 
                    status: message.status || job.status,
                    progress_percentage: message.progress || job.progress_percentage,
                    progress_message: message.message || job.progress_message,
                    error: message.error || job.error,
                  }
                : job
            )
          );
        }
        break;
        
      case 'pipeline_complete':
        if (message.pipeline_id === pipelineId) {
          setPipeline(prev => prev ? { ...prev, status: 'completed', overall_progress: 100 } : null);
          onComplete?.(message.result);
        }
        break;
        
      case 'pipeline_error':
        if (message.pipeline_id === pipelineId) {
          setPipeline(prev => prev ? { ...prev, status: 'failed' } : null);
          onError?.(message.error || 'Processing failed');
        }
        break;
        
      case 'pipeline_cancelled':
        if (message.pipeline_id === pipelineId) {
          setPipeline(prev => prev ? { ...prev, status: 'cancelled' } : null);
          onCancel?.();
        }
        break;
    }
  }

  // Load pipeline status from API
  const loadPipelineStatus = useCallback(async () => {
    try {
      const [pipelineStatus, pipelineJobs] = await Promise.all([
        processingApi.getProcessingStatus(pipelineId),
        processingApi.getPipelineJobs(pipelineId),
      ]);
      
      setPipeline(pipelineStatus);
      setJobs(pipelineJobs);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load processing status';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [pipelineId, onError]);

  // Initialize data loading
  useEffect(() => {
    loadPipelineStatus();
  }, [loadPipelineStatus]);

  // Handle cancel processing
  const handleCancelProcessing = useCallback(() => {
    Alert.alert(
      'Cancel Processing',
      'Are you sure you want to cancel email processing? This action cannot be undone.',
      [
        { text: 'Keep Processing', style: 'cancel' },
        { 
          text: 'Cancel Processing', 
          style: 'destructive',
          onPress: async () => {
            try {
              // Try WebSocket first for immediate feedback
              if (isConnected) {
                cancelPipeline(pipelineId);
              } else {
                // Fallback to API
                await processingApi.cancelProcessing(pipelineId);
              }
            } catch (err) {
              Alert.alert('Error', 'Failed to cancel processing');
            }
          }
        },
      ]
    );
  }, [pipelineId, isConnected, cancelPipeline]);

  // Handle retry failed jobs
  const handleRetryFailed = useCallback(() => {
    Alert.alert(
      'Retry Failed Jobs',
      'This will retry all failed jobs in this processing pipeline.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Retry', 
          onPress: () => {
            if (isConnected) {
              retryFailedJobs(pipelineId);
            } else {
              Alert.alert('Error', 'Real-time connection required for retry');
            }
          }
        },
      ]
    );
  }, [pipelineId, isConnected, retryFailedJobs]);

  // Get status color
  const getStatusColor = (status: string) => ProcessingUtils.getStatusColor(status);

  // Render loading state
  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading processing status...</Text>
      </View>
    );
  }

  // Render error state
  if (error || !pipeline) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>⚠️ {error || 'Pipeline not found'}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={loadPipelineStatus}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const estimatedTime = ProcessingUtils.estimateCompletionTime(pipeline);
  const canCancel = ProcessingUtils.canCancel(pipeline.status);
  const canRetry = ProcessingUtils.canRetry(pipeline.status);

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Processing Emails</Text>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(pipeline.status) }]}>
          <Text style={styles.statusText}>{ProcessingUtils.formatStatus(pipeline.status)}</Text>
        </View>
      </View>

      {/* Overall Progress */}
      <View style={styles.progressSection}>
        <View style={styles.progressHeader}>
          <Text style={styles.progressText}>
            Overall Progress: {pipeline.overall_progress}%
          </Text>
          {estimatedTime && (
            <Text style={styles.estimatedTime}>~{estimatedTime}</Text>
          )}
        </View>
        
        <View style={styles.progressBarContainer}>
          <View 
            style={[
              styles.progressBar, 
              { width: `${pipeline.overall_progress}%` }
            ]} 
          />
        </View>
        
        <Text style={styles.progressDetail}>
          Processing {pipeline.email_count} emails • {pipeline.jobs_completed} completed • {pipeline.jobs_failed} failed
        </Text>
      </View>

      {/* Job List */}
      <View style={styles.jobListSection}>
        <Text style={styles.sectionTitle}>Processing Steps</Text>
        {jobs.map((job) => (
          <View key={job.job_id} style={styles.jobItem}>
            <View style={styles.jobHeader}>
              <Text style={styles.jobType}>
                {ProcessingUtils.formatStatus(job.type)} - Email {job.email_id.slice(-8)}
              </Text>
              <View style={[styles.jobStatusBadge, { backgroundColor: getStatusColor(job.status) }]}>
                <Text style={styles.jobStatusText}>{ProcessingUtils.formatStatus(job.status)}</Text>
              </View>
            </View>
            
            <Text style={styles.jobMessage}>{job.progress_message}</Text>
            
            {job.status === 'processing' && (
              <View style={styles.jobProgressContainer}>
                <View style={styles.jobProgressBar}>
                  <View 
                    style={[
                      styles.jobProgressFill, 
                      { width: `${job.progress_percentage}%` }
                    ]} 
                  />
                </View>
                <Text style={styles.jobProgressText}>{job.progress_percentage}%</Text>
              </View>
            )}
            
            {job.error && (
              <Text style={styles.errorText}>Error: {job.error}</Text>
            )}
          </View>
        ))}
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        {canCancel && (
          <TouchableOpacity style={styles.cancelButton} onPress={handleCancelProcessing}>
            <Text style={styles.cancelButtonText}>Cancel Processing</Text>
          </TouchableOpacity>
        )}
        
        {canRetry && (
          <TouchableOpacity style={styles.retryButton} onPress={handleRetryFailed}>
            <Text style={styles.retryButtonText}>Retry Failed Jobs</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Connection Status */}
      <View style={styles.connectionStatus}>
        <View style={[styles.connectionIndicator, { 
          backgroundColor: isConnected ? '#34C759' : (wsError ? '#FF3B30' : '#FF9500') 
        }]} />
        <Text style={styles.connectionText}>
          {isConnected ? 'Real-time updates active' : 
           wsError ? 'Connection error' : 'Connecting...'}
        </Text>
        <Text style={styles.lastUpdateText}>
          Last update: {lastUpdate.toLocaleTimeString()}
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 15,
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 16,
    color: '#FF3B30',
    textAlign: 'center',
    marginBottom: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: 'white',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  statusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  progressSection: {
    backgroundColor: 'white',
    padding: 20,
    marginTop: 10,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  progressText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
  },
  estimatedTime: {
    fontSize: 14,
    color: '#666',
    fontStyle: 'italic',
  },
  progressBarContainer: {
    height: 8,
    backgroundColor: '#e9ecef',
    borderRadius: 4,
    marginBottom: 10,
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#007AFF',
    borderRadius: 4,
  },
  progressDetail: {
    fontSize: 14,
    color: '#666',
  },
  jobListSection: {
    backgroundColor: 'white',
    marginTop: 10,
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 15,
  },
  jobItem: {
    backgroundColor: '#f8f9fa',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
  },
  jobHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  jobType: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    flex: 1,
  },
  jobStatusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  jobStatusText: {
    color: 'white',
    fontSize: 10,
    fontWeight: 'bold',
  },
  jobMessage: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  jobProgressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  jobProgressBar: {
    flex: 1,
    height: 4,
    backgroundColor: '#e9ecef',
    borderRadius: 2,
    marginRight: 10,
  },
  jobProgressFill: {
    height: '100%',
    backgroundColor: '#34C759',
    borderRadius: 2,
  },
  jobProgressText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#007AFF',
    minWidth: 35,
    textAlign: 'right',
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 15,
    padding: 20,
  },
  cancelButton: {
    backgroundColor: '#FF3B30',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  cancelButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  retryButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  connectionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'white',
    padding: 15,
    marginTop: 10,
  },
  connectionIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  connectionText: {
    fontSize: 12,
    color: '#666',
    flex: 1,
    marginLeft: 8,
  },
  lastUpdateText: {
    fontSize: 10,
    color: '#999',
  },
});