import React from 'react';

const Footer: React.FC = () => (
  <footer className="bg-reroute-card border-t border-reroute-card py-4 text-center text-gray-400 text-sm flex flex-col items-center justify-center">
    <a
      href="https://www.strava.com"
      target="_blank"
      rel="noopener noreferrer"
      className="mb-2"
    >
      <img
        src="/src/assets/1.2-Strava-API-Logos/Powered by Strava/pwrdBy_strava_white/api_logo_pwrdBy_strava_horiz_white.svg"
        alt="Powered by Strava"
        style={{ height: '12px', display: 'inline-block' }}
      />
    </a>
    <span>&copy; {new Date().getFullYear()} Reroute. All rights reserved.</span>
  </footer>
);

export default Footer;
