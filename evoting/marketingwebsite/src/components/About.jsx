import React from 'react'
import { FaLock } from "react-icons/fa";
import Card from "./Card";


const About = () => {
  return (
    <div id="about" className='w-full h-full bg-white text-center'>
        <h1 className='text-2xl font-bold mt-16'>What is RingCT Technology?</h1>
        <p className='py-4 text-xl ml-24 mr-24 text-left'>
        Lorem ipsum dolor sit amet, consectetur adipisicing elit. 
        Blanditiis rem debitis cumque id atque tempora voluptas 
        delectus error, dignissimos pariatur eos saepe. Quis, 
        similique fugiat? Iure, sint amet! Temporibus, deleniti?
        Lorem ipsum dolor sit amet, consectetur adipisicing elit. 
        Blanditiis rem debitis cumque id atque tempora voluptas 
        delectus error, dignissimos pariatur eos saepe. Quis, 
        similique fugiat? Iure, sint amet! Temporibus, deleniti?
        Lorem ipsum dolor sit amet, consectetur adipisicing elit. 
        Blanditiis rem debitis cumque id atque tempora voluptas 
        delectus error, dignissimos pariatur eos saepe. Quis, 
        similique fugiat? Iure, sint amet! Temporibus, deleniti?
        </p>

        {/* Card Container */}
        <div className='py-12 grid sm:grid-cols-1 lg:grid-cols-3 gap-3'>

            {/* Card  */}
            <Card icon={< FaLock size={40}/>} heading='Anonymity' text='Lorem ipsum dolor sit amet consectetur adipisicing elit.
             A modi, quis enim suscipit sequi optio dolorem possimus fugit
            iste! Quibusdam, cum! Numquam nulla porro obcaecati quos debitis
            cum necessitatibus commodi.'/>

            <Card icon={<FaLock size={40}/>} heading='Linkability' text='Lorem ipsum dolor sit amet consectetur adipisicing elit.
             A modi, quis enim suscipit sequi optio dolorem possimus fugit
            iste! Quibusdam, cum! Numquam nulla porro obcaecati quos debitis
            cum necessitatibus commodi.'/>
            
            
            <Card icon={<FaLock size={40}/>} heading='Unforgeability' text='Lorem ipsum dolor sit amet consectetur adipisicing elit.
             A modi, quis enim suscipit sequi optio dolorem possimus fugit
            iste! Quibusdam, cum! Numquam nulla porro obcaecati quos debitis
            cum necessitatibus commodi.'/>

        </div>
    </div>
  )
}

export default About