import React, { useState, useEffect } from 'react';
import { 
  FaFacebookF,
  FaTwitter,
  FaInstagram,
  FaLinkedin,
  FaBars
} from 'react-icons/fa';


const Navbar = () => {
const [nav, setNav] = useState(false)

const handleNav = () => {
  setNav(!nav)
}
  return (
    <div className='w-full min-h-[50px] flex justify-between items-center absolute z-10 text-white bg-red-500/80'>
      <ul className='hidden sm:flex px-4'>
        <li>
          <a href='/'>Home</a>
        </li>
        <li>
          <a href='#about'>About</a>
        </li>
        <li>
          <a href='#info'>How Does It Work</a>
        </li>
        <li>
          <a href='#contact'>Meet The Team</a>
        </li>
        <li>
          <a href='#vote'>How to Vote</a>
        </li>
      </ul>
      <div className='flex justify-between'>
        <FaFacebookF className='mx-4' />
        <FaTwitter className='mx-4' />
        <FaInstagram className='mx-4' />
        <FaLinkedin className='mx-4' />
      </div>
        {/* Hamburger Icon */}
        <div onClick={handleNav} className='sm:hidden z-10'>
          <FaBars size={20} className='mr-4 cursor-pointer' />
        </div>
        {/* Mobile View */}
        <div 
        onClick={handleNav}
          className={
            nav
              ? 'overflow-y-hidden md:hidden ease-in duration-300 absolute text-gray-300 left-0 top-0 w-full h-screen bg-red-500/80 px-4 py-7 flex flex-col' 
              : 'absolute top-0 h-screen left-[-100%] ease-in duration-500'}>
        <ul className='h-full w-full text-center pt-12'>
          <li className='text-xl py-8'>
            <a href='/'>Home</a>
          </li>
          <li className='text-xl py-8'>
            <a href='#about'>About</a>
          </li>
          <li className='text-xl py-8'>
            <a href='#info'>How Does It Work</a>
          </li>
          <li className='text-xl py-8'>
            <a href='#contact'>Meet The Team</a>
          </li>
          <li className='text-xl py-8'>
            <a href='#vote'>How to Vote</a>
          </li>
        </ul>
        </div>
    </div>
  )
}

export default Navbar