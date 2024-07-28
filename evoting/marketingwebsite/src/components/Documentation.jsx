import React from 'react'
import Logo from '../assets/electSg_logo.png'
import TechDoc from '../assets/technicalDoc.png'
import UserGuide from '../assets/user-guide.png'
import UserManual from '../assets/UserManual.pdf'

const Documentation = () => {

    const handleDownload = () => {
        const link = document.createElement('a');
        link.download = 'User-Manual-PDF';
    
        link.href = UserManual;
    
        link.click();
      };

  return (
    <div id="documentation">
        <div className='py-4 text-2xl font-bold mt-16 mb-4 text-center'>Documentation</div>
        <div>
            <p className='py-4 text-xl mx-64 text-left'>This is the official documentation for our ElectSG e-voting platform. 
            This platform is designed to provide users a secure, efficient and trustworthy environment to participate in upcoming elections.
            Our system ensures that every vote remains anonymous and user privacy is maintained throughout the voting process.</p>
            <p className='py-4 text-xl mx-64 text-left'>The documentation listed below are intended for all users of the e-voting system, 
            from the voters who use the system, the system administrators who manage it and future developers who will help maintain it. 
            This will act as a comprehensive guide that offers information and instructions to help aid you in your efforts to use and
            manage the system effectively.</p>
        </div>
        <div className='col-span-2 justify-evenly flex flex-wrap'>
            <div className='w-[450px] text-left display block rounded-md border-2 mt-12 mb-1 p-8'>
                <img src={TechDoc} className='w-[100px] ml-[37%] my-2' />
                <h2 className='my-4 mx-14'>Technical Document</h2>
                <p>Lorem ipsum dolor sit amet consectetur adipisicing elit. Dolorum modi vel tempore, ullam et porro assumenda nobis ducimus voluptatem. 
                Maxime natus recusandae tempora ad fugiat consequuntur explicabo aliquid minus ab repudiandae aspernatur!</p>
                <button className='bg-red-500/80 text-white mt-6 mx-32 py-2 px-6 hover:bg-red-700 rounded-md' onClick={handleDownload}>Download</button>
            </div>
            <div className='w-[450px] text-left display block rounded-md border-2 mt-12 mb-1 p-8'>
                <img src={UserGuide} className='w-[100px] ml-[37%] my-2' />
                <h2 className='my-4 ml-[85px]'>Final User Manual</h2>
                <p>This user manual was designed to help guide new users on how to navigate through our e-voting platform. 
                This comprehensive guide will provide step-by-step instructions, as well as some troubleshooting tips to ensure
                a smooth and enjoyable voting experience.</p>
                <button className='bg-red-500/80 text-white mt-6 mx-32 py-2 px-6 hover:bg-red-700 rounded-md' onClick={handleDownload}>Download</button>
            </div>
        </div>
    </div>
  )
}

export default Documentation