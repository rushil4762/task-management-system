import React, { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { Sidebar } from '../components/layout/Sidebar';
import { Navbar } from '../components/layout/Navbar';
import { TaskModal } from '../components/tasks/TaskModal';

export const MainLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [newTaskModalOpen, setNewTaskModalOpen] = useState(false);
  const navigate = useNavigate();

  const handleTaskCreated = () => {
    // Dispatch custom event so active pages (TasksListPage, KanbanPage, DashboardPage) can refresh their data
    window.dispatchEvent(new Event('task:created'));
  };

  return (
    <div className="app-container">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="main-content">
        <Navbar
          onOpenSidebar={() => setSidebarOpen(true)}
          onNewTask={() => setNewTaskModalOpen(true)}
        />

        <main className="page-wrapper animate-fade-in">
          <Outlet />
        </main>
      </div>

      <TaskModal
        isOpen={newTaskModalOpen}
        onClose={() => setNewTaskModalOpen(false)}
        onSuccess={handleTaskCreated}
      />
    </div>
  );
};
