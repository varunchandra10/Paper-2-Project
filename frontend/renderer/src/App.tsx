import { Panel } from './components/panel/Panel';
import './App.css';

function App() {
  return (
    <div className="w-full h-full bg-[var(--bg-base)] text-[var(--text-main)] select-none relative flex flex-col overflow-hidden">
      <Panel />
    </div>
  );
}

export default App;
