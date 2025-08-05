import { useState, useEffect } from 'react';

// This custom hook takes a value and a delay time
export function useDebounce(value, delay) {
  // State to store the debounced value
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    // Set up a timer that will update the debounced value after the specified delay
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // This is the cleanup function. It runs every time the 'value' changes.
    // It clears the previous timer, so if the user is still typing, the
    // debounced value is never updated.
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]); // Only re-run the effect if the value or delay changes

  return debouncedValue;
}