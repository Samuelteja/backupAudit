import React from 'react';

function FilterBar({ filters, setFilters }) {
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFilters(prevFilters => ({
      ...prevFilters,
      [name]: value,
    }));
  };

  const handleClear = () => {
    setFilters({ alertName: '', severity: '' });
  };

  return (
    <div className="bg-gray-100 p-4 rounded-lg mb-6 flex items-center space-x-4">
      <span className="font-semibold text-gray-700">Filter by:</span>
      <input
        type="text"
        name="alertName"
        value={filters.alertName || ''}
        onChange={handleInputChange}
        placeholder="Alert Name..."
        className="px-3 py-2 border border-gray-300 rounded-md"
      />
      <select
        name="severity"
        value={filters.severity || ''}
        onChange={handleInputChange}
        className="px-3 py-2 border border-gray-300 rounded-md"
      >
        <option value="">All Severities</option>
        <option value="Critical">Critical</option>
        <option value="Major">Major</option>
        <option value="Warning">Warning</option>
        <option value="Minor">Minor</option>
      </select>
      <button onClick={handleClear} className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700">
        Clear
      </button>
    </div>
  );
}

export default FilterBar;