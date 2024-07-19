import React from 'react'
import Logo from "../assets/electSg_logo.png"
import {AiFillPhone, AiOutlineClockCircle} from "react-icons/ai"
import { MdOutlineMail } from "react-icons/md"


const Topbar = () => {
  return (
    <div className='flex justify-between items-center px-4 py-2'>
        <div className='flex items-center'>
            <img className='h-20 max-w-xs px-8' src={Logo}/>
        </div>
        <div className='flex'>
            <div className='hidden md:flex items-center px-6'>
                <AiOutlineClockCircle size={20} className='mr-2'/>
                <p>9AM - 5PM</p>
            </div>

            <div className='hidden md:flex items-center px-6'>
                <AiFillPhone size={20} className='mr-2'/>
                <p>1234-5678</p>
            </div>

            <div className='hidden md:flex items-center px-6'>
                <MdOutlineMail size={20} className='mr-2'/>
                <p>electsg@gmail.com</p>
            </div>
        </div>
    </div>
  )
}

export default Topbar