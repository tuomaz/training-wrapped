import { useState, useEffect } from 'react';
import { Slide } from './components/Slide';
import { Dumbbell, Activity, Trophy, Bike, Footprints, Flame, Clock, Zap } from 'lucide-react';
import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import wrappedData from './data/wrapped_data.json';

interface WrappedData {
  year: number;
  summary: {
    total_sessions: number;
    total_km: number;
    total_km_run: number;
    total_km_cycle: number;
    total_gym: number;
    total_cardio: number;
    total_hours: number;
  };
  highlights: {
    longest_run: number;
    longest_ride: number;
    most_active_month: string;
    top_exercises: string[];
    longest_streak: number;
    best_run_week: { week: number; distance: number };
    best_cycle_week: { week: number; distance: number };
    best_gym_month: { month: number; count: number };
    top_5_longest_runs: { date: string; distance_km: number }[];
    top_5_fastest_runs: { date: string; distance_km: number; speed_kmh: number; pace: string }[];
    top_5_longest_rides: { date: string; distance_km: number }[];
    top_5_fastest_rides: { date: string; distance_km: number; speed_kmh: number }[];
  };
  charts: {
    monthly: { month: number; run: number; cycle: number; gym: number; total: number }[];
    day_of_week: { day: string; count: number }[];
  };
}

function App() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const totalSlides = 10; 
  const data = wrappedData as unknown as WrappedData;

  const nextSlide = () => setCurrentSlide((prev) => (prev + 1) % totalSlides);
  const prevSlide = () => setCurrentSlide((prev) => (prev - 1 + totalSlides) % totalSlides);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') nextSlide();
      if (e.key === 'ArrowLeft') prevSlide();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const monthNames = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const monthlyChartData = data.charts.monthly.map(d => ({ ...d, name: monthNames[d.month] })).sort((a,b) => a.month - b.month);

  return (
    <div className="relative w-full h-screen overflow-hidden bg-black text-white" onClick={nextSlide}>
      {/* Progress Bar */}
      <div className="absolute top-0 left-0 right-0 flex gap-1 p-2 z-50">
        {Array.from({ length: totalSlides }).map((_, idx) => (
          <div 
            key={idx} 
            className={`h-1 flex-1 rounded-full transition-colors ${idx <= currentSlide ? 'bg-white' : 'bg-gray-800'}`} 
          />
        ))}
      </div>

      {/* Slide 1: Intro */}
      <Slide isActive={currentSlide === 0} color="bg-gradient-to-br from-purple-900 to-black">
        <h1 className="text-6xl font-black mb-4">2025</h1>
        <h2 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-500 to-yellow-500">
          TRAINING WRAPPED
        </h2>
        <p className="mt-8 text-xl text-gray-400 animate-pulse">Tap or use arrow keys</p>
      </Slide>

      {/* Slide 2: The Big Numbers */}
      <Slide isActive={currentSlide === 1} color="bg-black">
        <h2 className="text-3xl font-bold mb-12 text-blue-400">The Grind</h2>
        <div className="grid grid-cols-2 gap-8 w-full max-w-2xl">
          <div className="bg-gray-900 p-8 rounded-2xl border border-gray-800">
            <Activity className="w-12 h-12 text-green-400 mb-4 mx-auto" />
            <div className="text-5xl font-black">{data.summary.total_sessions}</div>
            <div className="text-gray-400 uppercase tracking-widest text-sm mt-2">Total Sessions</div>
          </div>
          <div className="bg-gray-900 p-8 rounded-2xl border border-gray-800">
            <Clock className="w-12 h-12 text-yellow-400 mb-4 mx-auto" />
            <div className="text-5xl font-black">{Math.round(data.summary.total_hours)}</div>
            <div className="text-gray-400 uppercase tracking-widest text-sm mt-2">Hours Sweating</div>
          </div>
        </div>
      </Slide>

      {/* Slide 3: Consistency & Streak */}
      <Slide isActive={currentSlide === 2} color="bg-gray-900">
        <h2 className="text-3xl font-bold mb-8 text-orange-500">Unstoppable</h2>
        <Flame className="w-24 h-24 text-orange-500 mb-4 animate-bounce" />
        <div className="text-8xl font-black mb-2">{data.highlights.longest_streak}</div>
        <div className="text-xl uppercase tracking-widest mb-12">Day Streak</div>
        <p className="text-gray-400 text-lg">You showed up correctly.</p>
      </Slide>

      {/* Slide 4: Monthly Breakdown Chart (Stacked) */}
      <Slide isActive={currentSlide === 3} color="bg-black">
        <h2 className="text-3xl font-bold mb-8 text-purple-400">Year in Review</h2>
        <div className="w-full max-w-4xl h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={monthlyChartData}>
              <XAxis dataKey="name" stroke="#888" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#111', border: 'none' }}
                cursor={{ fill: '#222' }}
              />
              <Legend verticalAlign="top" height={36}/>
              <Bar dataKey="run" stackId="a" fill="#06b6d4" name="Running" />
              <Bar dataKey="cycle" stackId="a" fill="#22c55e" name="Cycling" />
              <Bar dataKey="gym" stackId="a" fill="#ec4899" name="Gym" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p className="mt-8 text-gray-500">Sessions per Month</p>
      </Slide>

      {/* Slide 5: Peak Performance (New) */}
      <Slide isActive={currentSlide === 4} color="bg-gray-900">
        <h2 className="text-3xl font-bold mb-10 text-yellow-500">Peak Performance</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
           {/* Best Run Week */}
           <div className="bg-gray-800 p-6 rounded-xl flex flex-col items-center">
             <Zap className="text-cyan-400 mb-4 w-10 h-10" />
             <div className="text-3xl font-bold">{data.highlights.best_run_week.distance.toFixed(0)} km</div>
             <div className="text-xs uppercase text-gray-400 mt-2">Best Run Week</div>
             <div className="text-xs text-gray-500 mt-1">Week {data.highlights.best_run_week.week}</div>
           </div>
           
           {/* Best Bike Week */}
           <div className="bg-gray-800 p-6 rounded-xl flex flex-col items-center">
             <Bike className="text-green-400 mb-4 w-10 h-10" />
             <div className="text-3xl font-bold">{data.highlights.best_cycle_week.distance.toFixed(0)} km</div>
             <div className="text-xs uppercase text-gray-400 mt-2">Best Bike Week</div>
             <div className="text-xs text-gray-500 mt-1">Week {data.highlights.best_cycle_week.week}</div>
           </div>

           {/* Best Gym Month */}
           <div className="bg-gray-800 p-6 rounded-xl flex flex-col items-center">
             <Dumbbell className="text-pink-500 mb-4 w-10 h-10" />
             <div className="text-3xl font-bold">{data.highlights.best_gym_month.count}</div>
             <div className="text-xs uppercase text-gray-400 mt-2">Sessions in {monthNames[data.highlights.best_gym_month.month]}</div>
             <div className="text-xs text-gray-500 mt-1">Best Gym Month</div>
           </div>
        </div>
      </Slide>

      {/* Slide 6: Gym Stats */}
      <Slide isActive={currentSlide === 5} color="bg-gray-900">
        <h2 className="text-3xl font-bold mb-8 text-pink-500">Iron Paradise</h2>
        <Dumbbell className="w-16 h-16 text-pink-500 mb-6" />
        <div className="text-6xl font-black mb-4">{data.summary.total_gym}</div>
        <div className="text-lg uppercase tracking-widest mb-8">Gym Sessions</div>
        
        <div className="bg-black/50 p-6 rounded-xl w-full max-w-md border border-pink-500/20">
          <h3 className="text-gray-400 text-xs uppercase mb-4 tracking-widest">Most Frequent Lifts</h3>
          <div className="space-y-4">
            {data.highlights.top_exercises.map((ex, i) => (
              <div key={i} className="flex items-center justify-between text-lg font-medium">
                <span>{ex}</span>
                <span className="text-pink-500 font-bold">#{i+1}</span>
              </div>
            ))}
          </div>
        </div>
      </Slide>

      {/* Slide 7: Cardio Stats */}
      <Slide isActive={currentSlide === 6} color="bg-gradient-to-b from-blue-900 to-black">
        <h2 className="text-3xl font-bold mb-12 text-cyan-400">On The Move</h2>
        <div className="grid grid-cols-2 gap-8 w-full max-w-3xl">
           {/* Run Stats */}
           <div className="flex flex-col items-center">
              <Footprints className="w-12 h-12 text-cyan-400 mb-2" />
              <span className="text-gray-400 text-sm uppercase tracking-widest mb-2">Longest Run</span>
              <span className="text-4xl font-black">{data.highlights.longest_run.toFixed(1)} km</span>
           </div>

           {/* Ride Stats */}
           <div className="flex flex-col items-center">
              <Bike className="w-12 h-12 text-green-400 mb-2" />
              <span className="text-gray-400 text-sm uppercase tracking-widest mb-2">Longest Ride</span>
              <span className="text-4xl font-black">{data.highlights.longest_ride.toFixed(1)} km</span>
           </div>
        </div>

        <div className="mt-16 text-center">
          <div className="text-7xl font-black text-white">{Math.round(data.summary.total_km)}</div>
          <div className="text-cyan-400 uppercase tracking-widest mt-2">Total Kilometers</div>
        </div>
      </Slide>

      {/* Slide 8: Running PRs */}
      <Slide isActive={currentSlide === 7} color="bg-black">
        <h2 className="text-3xl font-bold mb-8 text-cyan-400">Running Hall of Fame</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl">
          {/* Longest Runs */}
          <div className="bg-gray-900/50 p-6 rounded-2xl border border-cyan-900/30">
            <h3 className="text-cyan-400 text-sm uppercase tracking-widest mb-4 flex items-center gap-2">
              <Footprints className="w-4 h-4" /> Top 5 Distance
            </h3>
            <div className="space-y-3">
              {data.highlights.top_5_longest_runs.map((run, i) => (
                <div key={i} className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">{run.date}</span>
                  <span className="font-bold">{run.distance_km.toFixed(1)} km</span>
                </div>
              ))}
            </div>
          </div>

          {/* Fastest Runs */}
          <div className="bg-gray-900/50 p-6 rounded-2xl border border-yellow-900/30">
            <h3 className="text-yellow-500 text-sm uppercase tracking-widest mb-4 flex items-center gap-2">
              <Zap className="w-4 h-4" /> Top 5 Speed
            </h3>
            <div className="space-y-3">
              {data.highlights.top_5_fastest_runs.map((run, i) => (
                <div key={i} className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">{run.date}</span>
                  <span className="font-bold">{run.pace} /km</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Slide>

      {/* Slide 9: Biking PRs */}
      <Slide isActive={currentSlide === 8} color="bg-black">
        <h2 className="text-3xl font-bold mb-8 text-green-400">Cycling Hall of Fame</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl">
          {/* Longest Rides */}
          <div className="bg-gray-900/50 p-6 rounded-2xl border border-green-900/30">
            <h3 className="text-green-400 text-sm uppercase tracking-widest mb-4 flex items-center gap-2">
              <Bike className="w-4 h-4" /> Top 5 Distance
            </h3>
            <div className="space-y-3">
              {data.highlights.top_5_longest_rides.map((ride, i) => (
                <div key={i} className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">{ride.date}</span>
                  <span className="font-bold">{ride.distance_km.toFixed(1)} km</span>
                </div>
              ))}
            </div>
          </div>

          {/* Fastest Rides */}
          <div className="bg-gray-900/50 p-6 rounded-2xl border border-yellow-900/30">
            <h3 className="text-yellow-500 text-sm uppercase tracking-widest mb-4 flex items-center gap-2">
              <Zap className="w-4 h-4" /> Top 5 Speed
            </h3>
            <div className="space-y-3">
              {data.highlights.top_5_fastest_rides.map((ride, i) => (
                <div key={i} className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">{ride.date}</span>
                  <span className="font-bold">{ride.speed_kmh.toFixed(1)} km/h</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Slide>

      {/* Slide 10: Outro */}
      <Slide isActive={currentSlide === 9} color="bg-black">
        <Trophy className="w-32 h-32 text-yellow-400 mb-8 animate-bounce" />
        <h1 className="text-5xl font-bold mb-4">You Crushed It!</h1>
        <p className="text-2xl text-gray-400">See you in 2026.</p>
        <div className="mt-12 flex gap-4 text-gray-600 text-sm">
           <span>{data.charts.day_of_week.sort((a,b) => b.count - a.count)[0]?.day}s are your power days.</span>
        </div>
      </Slide>
    </div>
  );
}

export default App;