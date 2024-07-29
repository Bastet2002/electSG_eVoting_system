import React from 'react'
import UserManual from '../assets/UserManual.pdf'
import NationalDay from '../assets/National_Day.png'
import ReactPlayer from 'react-player'
import VideoPlayer from './VideoPlayer'



const Info = () => {

    const handleDownload = () => {
        const link = document.createElement('a');
        link.download = 'User-Manual-PDF';
    
        link.href = UserManual;
    
        link.click();
      };

      

  return (

    <div id="info" className='bg-white'>
        <h1 className='py-4 text-2xl font-bold mt-12 mb-4 text-center'>How Does It Work?</h1>
        <div className='display: flex items-center justify-between'>
            <div className='ml-12 w-[40%] text-xl'>Lorem ipsum dolor sit amet consectetur adipisicing elit. Itaque veritatis rerum reiciendis neque, 
            quam pariatur at quasi tempore animi deleniti, et nobis dolores, doloribus sapiente provident necessitatibus
            fuga odit dolorem! Lorem ipsum dolor sit amet consectetur adipisicing elit. Itaque veritatis rerum reiciendis neque, 
            quam pariatur at quasi tempore animi deleniti, et nobis dolores, doloribus sapiente provident necessitatibus fuga
            </div>
            <div className='position: relative w-[50%] display: flex justify-between z-[99] m-8'>
                <img className='w-[49%] h-[450px] rounded-md object-cover info-shadow-custom' src={NationalDay}/>
                <img className='w-[49%] h-[450px] rounded-md object-cover info-shadow-custom position: absolute top-[-10%] right-0' src={NationalDay}/>
            </div>
        </div>
        <div className='grid grid-cols-2'>
        <div className='mt-12 ml-8'>
            <VideoPlayer />
        </div>
            <div className='mt-12 p-[50px]'>
                <h2 className='text-4xl mb-4 ml-4 text-stone-800/80'>Simple. Safe. Secure.</h2>
                <h3 className='text-xl font-semibold mx-4'>Singapore's first E-Voting platform with RingCT implementation</h3>
                <h4 className='mt-4 ml-4 font-weight italic text-m'>Empowering Your Vote with Cutting-Edge Privacy</h4>
                <button className='bg-red-500/80 text-white mt-12 mx-32 py-4 px-2 hover:bg-red-700 rounded-md' onClick={handleDownload}>Click here for more information</button>
            </div>
        </div>
        </div>
  );
}

export default Info