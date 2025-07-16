import React, { useState } from 'react';
import { Search, Filter, MapPin, Heart, Share2, Download, Star } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

interface Route {
  id: string;
  name: string;
  description: string;
  distance: string;
  duration: string;
  elevation: string;
  difficulty: 'Easy' | 'Moderate' | 'Hard' | 'Expert';
  type: 'Road' | 'Gravel' | 'Mountain' | 'Urban';
  rating: number;
  reviews: number;
  isFavorite: boolean;
  image: string;
  tags: string[];
}

const Routes: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');

  const routes: Route[] = [
    {
      id: '1',
      name: 'Scenic Lake Loop',
      description: 'Beautiful route around the lake with stunning views and gentle climbs.',
      distance: '45.2 km',
      duration: '2h 15m',
      elevation: '320m',
      difficulty: 'Moderate',
      type: 'Road',
      rating: 4.8,
      reviews: 127,
      isFavorite: true,
      image: '/api/placeholder/400/200',
      tags: ['Scenic', 'Lake', 'Popular']
    },
    {
      id: '2',
      name: 'Mountain Challenge',
      description: 'Epic climb with breathtaking summit views. Not for the faint-hearted!',
      distance: '68.4 km',
      duration: '4h 30m',
      elevation: '1,250m',
      difficulty: 'Expert',
      type: 'Road',
      rating: 4.9,
      reviews: 89,
      isFavorite: false,
      image: '/api/placeholder/400/200',
      tags: ['Mountain', 'Challenge', 'Epic']
    },
    {
      id: '3',
      name: 'Urban Explorer',
      description: 'City route through historic districts and modern architecture.',
      distance: '28.6 km',
      duration: '1h 45m',
      elevation: '150m',
      difficulty: 'Easy',
      type: 'Urban',
      rating: 4.2,
      reviews: 203,
      isFavorite: false,
      image: '/api/placeholder/400/200',
      tags: ['Urban', 'Historic', 'City']
    },
    {
      id: '4',
      name: 'Gravel Adventure',
      description: 'Off-road adventure through forests and countryside paths.',
      distance: '52.8 km',
      duration: '3h 20m',
      elevation: '480m',
      difficulty: 'Hard',
      type: 'Gravel',
      rating: 4.6,
      reviews: 156,
      isFavorite: true,
      image: '/api/placeholder/400/200',
      tags: ['Gravel', 'Adventure', 'Forest']
    },
    {
      id: '5',
      name: 'Coastal Cruise',
      description: 'Relaxing ride along the coastline with ocean views.',
      distance: '38.9 km',
      duration: '2h 05m',
      elevation: '180m',
      difficulty: 'Easy',
      type: 'Road',
      rating: 4.7,
      reviews: 234,
      isFavorite: false,
      image: '/api/placeholder/400/200',
      tags: ['Coastal', 'Scenic', 'Relaxing']
    },
    {
      id: '6',
      name: 'Hill Training',
      description: 'Perfect route for hill training with multiple climbs.',
      distance: '42.3 km',
      duration: '2h 45m',
      elevation: '650m',
      difficulty: 'Hard',
      type: 'Road',
      rating: 4.4,
      reviews: 98,
      isFavorite: false,
      image: '/api/placeholder/400/200',
      tags: ['Training', 'Hills', 'Climbs']
    }
  ];

  const difficulties = ['all', 'Easy', 'Moderate', 'Hard', 'Expert'];
  const types = ['all', 'Road', 'Gravel', 'Mountain', 'Urban'];

  const filteredRoutes = routes.filter(route => {
    const matchesSearch = route.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         route.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         route.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesDifficulty = selectedDifficulty === 'all' || route.difficulty === selectedDifficulty;
    const matchesType = selectedType === 'all' || route.type === selectedType;
    
    return matchesSearch && matchesDifficulty && matchesType;
  });

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Easy': return 'bg-reroute-green/20 text-reroute-green';
      case 'Moderate': return 'bg-reroute-yellow/20 text-reroute-yellow';
      case 'Hard': return 'bg-reroute-red/20 text-reroute-red';
      case 'Expert': return 'bg-reroute-purple/20 text-reroute-purple';
      default: return 'bg-reroute-card text-gray-400';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'Road': return 'bg-reroute-primary/20 text-reroute-primary';
      case 'Gravel': return 'bg-reroute-yellow/20 text-reroute-yellow';
      case 'Mountain': return 'bg-reroute-purple/20 text-reroute-purple';
      case 'Urban': return 'bg-reroute-card text-gray-400';
      default: return 'bg-reroute-card text-gray-400';
    }
  };

  return (
    <div className="">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Routes</h1>
          <p className="text-gray-400 mt-2">Discover and plan your next cycling adventure</p>
        </div>

        {/* Search and Filters */}
        <div className="mb-8 space-y-4">
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input
              type="text"
              placeholder="Search routes by name, description, or tags..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-reroute-card text-white placeholder-gray-400 border-reroute-gray"
            />
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <span className="text-sm font-medium text-gray-300">Difficulty:</span>
              <div className="flex space-x-2">
                {difficulties.map((difficulty) => (
                  <button
                    key={difficulty}
                    onClick={() => setSelectedDifficulty(difficulty)}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                      selectedDifficulty === difficulty
                        ? 'bg-reroute-primary text-white'
                        : 'bg-reroute-card text-gray-400 hover:bg-reroute-card/80'
                    }`}
                  >
                    {difficulty === 'all' ? 'All' : difficulty}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-300">Type:</span>
              <div className="flex space-x-2">
                {types.map((type) => (
                  <button
                    key={type}
                    onClick={() => setSelectedType(type)}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                      selectedType === type
                        ? 'bg-reroute-primary text-white'
                        : 'bg-reroute-card text-gray-400 hover:bg-reroute-card/80'
                    }`}
                  >
                    {type === 'all' ? 'All' : type}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Routes Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredRoutes.map((route) => (
            <Card key={route.id} className="bg-reroute-card border-reroute-card hover:shadow-card transition-shadow">
              <CardHeader className="pb-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-white text-lg">{route.name}</CardTitle>
                    <p className="text-gray-400 text-sm mt-1">{route.description}</p>
                  </div>
                  <button
                    className={`p-2 rounded-full transition-colors ${
                      route.isFavorite 
                        ? 'text-reroute-red hover:text-reroute-red/80' 
                        : 'text-gray-400 hover:text-reroute-red'
                    }`}
                  >
                    <Heart className={`w-5 h-5 ${route.isFavorite ? 'fill-current' : ''}`} />
                  </button>
                </div>
              </CardHeader>

              <CardContent>
                {/* Route Stats */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center">
                    <p className="text-white font-semibold">{route.distance}</p>
                    <p className="text-gray-400 text-xs">Distance</p>
                  </div>
                  <div className="text-center">
                    <p className="text-white font-semibold">{route.duration}</p>
                    <p className="text-gray-400 text-xs">Duration</p>
                  </div>
                  <div className="text-center">
                    <p className="text-white font-semibold">{route.elevation}</p>
                    <p className="text-gray-400 text-xs">Elevation</p>
                  </div>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-2 mb-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(route.difficulty)}`}>
                    {route.difficulty}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(route.type)}`}>
                    {route.type}
                  </span>
                  {route.tags.slice(0, 2).map((tag) => (
                    <span key={tag} className="px-2 py-1 rounded-full text-xs font-medium bg-reroute-card text-gray-400">
                      {tag}
                    </span>
                  ))}
                </div>

                {/* Rating */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-1">
                    <Star className="w-4 h-4 text-reroute-yellow fill-current" />
                    <span className="text-white font-medium">{route.rating}</span>
                    <span className="text-gray-400 text-sm">({route.reviews} reviews)</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex space-x-2">
                  <Button className="flex-1 bg-reroute-primary hover:bg-reroute-primary/80 text-white">
                    <MapPin className="w-4 h-4 mr-2" />
                    View Route
                  </Button>
                  <Button variant="outline" size="sm" className="border-reroute-gray text-white hover:bg-reroute-card">
                    <Share2 className="w-4 h-4" />
                  </Button>
                  <Button variant="outline" size="sm" className="border-reroute-gray text-white hover:bg-reroute-card">
                    <Download className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredRoutes.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-400">No routes found matching your criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Routes; 