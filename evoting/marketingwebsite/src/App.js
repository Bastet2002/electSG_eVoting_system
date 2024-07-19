import React from "react";
import Topbar from "./components/Topbar";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import About from "./components/About";
import Info from "./components/Info";
import Contact from "./components/Contact";
import Vote from "./components/Vote";
import Newsletter from "./components/Newsletter";

function App() {
  return (
    <div>
      <Topbar/>
      <Navbar/>
      <Hero />
      <About/>
      <Info />
      <Contact />
      <Vote />
      <Newsletter />
    </div>
  );
}

export default App;
