import React from 'react';

const Footer: React.FC = () => (
  <footer className="bg-reroute-card border-t border-reroute-card py-4 text-center text-gray-400 text-sm">
    &copy; {new Date().getFullYear()} Reroute. All rights reserved.
  </footer>
);

export default Footer; 