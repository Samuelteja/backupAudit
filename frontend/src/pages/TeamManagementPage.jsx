// frontend/src/pages/TeamManagementPage.jsx
import React, { useState, useEffect } from 'react';
import { getTenantUsers, inviteUser } from '../services/api';
import { useAuth } from '../context/useAuth';

function TeamManagementPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // State for the invite form
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('viewer');
  const [inviteError, setInviteError] = useState(null);
  const [inviteSuccess, setInviteSuccess] = useState('');

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      const response = await getTenantUsers();
      setUsers(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch team members.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleInvite = async (e) => {
    e.preventDefault();
    setInviteError(null);
    setInviteSuccess('');
    try {
      await inviteUser(inviteEmail, inviteRole);
      setInviteSuccess(`Successfully invited ${inviteEmail}.`);
      setInviteEmail(''); // Clear form
      fetchUsers(); // Refresh the user list
    } catch (err) {
      setInviteError(err.response?.data?.detail || 'Failed to send invitation.');
    }
  };

  const renderInviteForm = () => {
    if (user?.role !== 'owner' && user?.role !== 'admin') return null;

    return (
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-semibold mb-4">Invite New User</h3>
        <form onSubmit={handleInvite} className="flex items-end space-x-4">
          <div className="flex-grow">
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
            <input type="email" value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} required className="w-full mt-1 border border-gray-300 rounded-md p-2" />
          </div>
          <div>
            <label htmlFor="role" className="block text-sm font-medium text-gray-700">Role</label>
            <select value={inviteRole} onChange={(e) => setInviteRole(e.target.value)} className="mt-1 border border-gray-300 rounded-md p-2">
              <option value="viewer">Viewer</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">Invite</button>
        </form>
        {inviteError && <p className="text-red-500 mt-2">{inviteError}</p>}
        {inviteSuccess && <p className="text-green-500 mt-2">{inviteSuccess}</p>}
      </div>
    );
  };

  if (isLoading) return <p>Loading team members...</p>;
  if (error) return <p className="text-red-500">{error}</p>;

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-gray-800 mb-8">Team Management</h1>
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        {renderInviteForm()}
        <table className="min-w-full divide-y divide-gray-200">
          {/* ... table head ... */}
          <tbody className="bg-white divide-y divide-gray-200">
            {users.map(user => (
              <tr key={user.id}>
                <td className="px-6 py-4">{user.email}</td>
                <td className="px-6 py-4">{user.role}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default TeamManagementPage;