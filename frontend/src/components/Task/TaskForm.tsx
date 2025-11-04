import React, { useState, useEffect } from 'react';
import Modal from 'react-modal';
import { useCreateTaskMutation, useUpdateTaskMutation } from '@/services/taskApi';
import type { Task, TaskCreate, TaskUpdate } from '@/types/task';

interface TaskFormProps {
  task?: Task | null;
  emailId?: string;
  onClose: () => void;
  isOpen: boolean;
}

// Make sure to bind modal to your appElement (http://reactcommunity.org/react-modal/accessibility/)
if (typeof window !== 'undefined' && process.env.NODE_ENV !== 'test') {
  const rootElement = document.getElementById('root');
  if (rootElement) {
    Modal.setAppElement('#root');
  }
}

export const TaskForm: React.FC<TaskFormProps> = ({ task, emailId, onClose, isOpen }) => {
  const [createTask, { isLoading: isCreating }] = useCreateTaskMutation();
  const [updateTask, { isLoading: isUpdating }] = useUpdateTaskMutation();
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium' as 'high' | 'medium' | 'low',
    category: 'required_action' as Task['category'],
    due_date: '',
    tags: [] as string[],
    progress: 0,
  });

  const [tagInput, setTagInput] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const isEditing = !!task;
  const isLoading = isCreating || isUpdating;

  useEffect(() => {
    if (task) {
      setFormData({
        title: task.title,
        description: task.description || '',
        priority: task.priority,
        category: task.category,
        due_date: task.due_date || '',
        tags: task.tags || [],
        progress: task.progress || 0,
      });
    } else {
      // Reset form for creation
      setFormData({
        title: '',
        description: '',
        priority: 'medium',
        category: 'required_action',
        due_date: '',
        tags: [],
        progress: 0,
      });
    }
    setErrors({});
  }, [task, isOpen]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }
    
    if (formData.due_date && new Date(formData.due_date) < new Date()) {
      newErrors.due_date = 'Due date cannot be in the past';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      if (isEditing && task) {
        const updateData: TaskUpdate = {
          title: formData.title,
          description: formData.description || undefined,
          priority: formData.priority,
          due_date: formData.due_date || undefined,
          tags: formData.tags,
          progress: formData.progress,
        };
        await updateTask({ id: task.id, data: updateData }).unwrap();
      } else {
        const createData: TaskCreate & { email_id?: string } = {
          title: formData.title,
          description: formData.description || undefined,
          priority: formData.priority,
          category: formData.category,
          due_date: formData.due_date || undefined,
          tags: formData.tags,
          email_id: emailId,
        };
        await createTask(createData).unwrap();
      }
      
      onClose();
    } catch (error) {
      console.error('Failed to save task:', error);
      setErrors({ submit: 'Failed to save task. Please try again.' });
    }
  };

  const handleTagAdd = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      const newTag = tagInput.trim();
      if (!formData.tags.includes(newTag)) {
        setFormData(prev => ({
          ...prev,
          tags: [...prev.tags, newTag]
        }));
      }
      setTagInput('');
    }
  };

  const handleTagRemove = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  return (
    <Modal
      isOpen={isOpen}
      onRequestClose={onClose}
      contentLabel={isEditing ? 'Edit Task' : 'Create Task'}
      className="task-form-modal"
      overlayClassName="task-form-overlay"
    >
      <div className="task-form">
        <div className="form-header">
          <h2>{isEditing ? 'Edit Task' : 'Create New Task'}</h2>
          <button 
            className="close-btn"
            onClick={onClose}
            disabled={isLoading}
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="title">Title *</label>
            <input
              id="title"
              type="text"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              disabled={isLoading}
              className={errors.title ? 'error' : ''}
              data-testid="task-title-input"
            />
            {errors.title && <span className="error-text">{errors.title}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              disabled={isLoading}
              rows={3}
              data-testid="task-description-input"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="priority">Priority</label>
              <select
                id="priority"
                value={formData.priority}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  priority: e.target.value as 'high' | 'medium' | 'low' 
                }))}
                disabled={isLoading}
                data-testid="task-priority-select"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>

            {!isEditing && (
              <div className="form-group">
                <label htmlFor="category">Category</label>
                <select
                  id="category"
                  value={formData.category}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    category: e.target.value as Task['category']
                  }))}
                  disabled={isLoading}
                >
                  <option value="required_action">Required Action</option>
                  <option value="team_action">Team Action</option>
                  <option value="job_listing">Job Listing</option>
                  <option value="optional_event">Optional Event</option>
                  <option value="fyi">FYI</option>
                </select>
              </div>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="due_date">Due Date</label>
              <input
                id="due_date"
                type="datetime-local"
                value={formData.due_date}
                onChange={(e) => setFormData(prev => ({ ...prev, due_date: e.target.value }))}
                disabled={isLoading}
                className={errors.due_date ? 'error' : ''}
              />
              {errors.due_date && <span className="error-text">{errors.due_date}</span>}
            </div>

            {isEditing && (
              <div className="form-group">
                <label htmlFor="progress">Progress (%)</label>
                <input
                  id="progress"
                  type="number"
                  min="0"
                  max="100"
                  value={formData.progress}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    progress: Math.max(0, Math.min(100, parseInt(e.target.value) || 0))
                  }))}
                  disabled={isLoading}
                />
              </div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="tags">Tags</label>
            <input
              id="tags"
              type="text"
              placeholder="Type a tag and press Enter"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={handleTagAdd}
              disabled={isLoading}
            />
            <div className="tags-list">
              {formData.tags.map(tag => (
                <span key={tag} className="tag">
                  {tag}
                  <button
                    type="button"
                    onClick={() => handleTagRemove(tag)}
                    disabled={isLoading}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {errors.submit && (
            <div className="error-message">{errors.submit}</div>
          )}

          <div className="form-actions">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="btn-secondary"
              data-testid="task-cancel-button"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary"
              data-testid="task-submit-button"
            >
              {isLoading ? 'Saving...' : (isEditing ? 'Update Task' : 'Create Task')}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
};