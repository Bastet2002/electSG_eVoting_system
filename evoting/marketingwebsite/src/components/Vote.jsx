import React from 'react'
import Logo from '../assets/electSg_logo.png'
import UserManual from '../assets/UserManual.pdf'

const Vote = () => {

    const handleDownload = () => {
        const link = document.createElement('a');
        link.download = 'User-Manual-PDF';
    
        link.href = UserManual;
    
        link.click();
      };
 
    
  return (
    <div id="vote">
        <div className='py-4 text-2xl font-bold mt-16 mb-4 text-center'>How to Vote</div>
        <div className='text-center text-xl'>
            <p>In order to be eligible for voting, you must meet these certain criteria:</p>
        </div>
        <div className='mt-12 mx-auto text-left w-[40%] text-xl leading-9'>
            <p>1. You must be a Singapore Citizen <span className='font-bold'>and</span> holder of a pink IC.</p>
            <p>2. You must be older than the age of <span className='font-bold'>21</span>.</p>
            <p>3. You have not been disqualified from being an elector under any preveiling law.</p>
            <p>4. You must have a Singapore <span className='font-bold'>residential address</span> on your NRIC.</p>
        </div>
        <div className='col-span-3 justify-evenly flex flex-wrap'>
        <div className='w-[300px] text-center display block rounded-md border-2 mt-12 mr-[10px] mb-1'>
            <img src={Logo} />
            <p>Lorem ipsum, dolor sit amet consectetur adipisicing elit. Adipisci officia aut aspernatur veniam architecto aliquam earum, nulla quo consequuntur numquam!</p>
        </div>
        <div className='w-[300px] text-center display block rounded-md border-2 mt-12 mr-[10px] mb-1'>
            <img src={Logo} />
            <p>Lorem ipsum, dolor sit amet consectetur adipisicing elit. Adipisci officia aut aspernatur veniam architecto aliquam earum, nulla quo consequuntur numquam!</p>
        </div>
        <div className='w-[300px] text-center display block rounded-md border-2 mt-12 mr-[10px] mb-1'>
            <img src={Logo} />
            <p>Lorem ipsum, dolor sit amet consectetur adipisicing elit. Adipisci officia aut aspernatur veniam architecto aliquam earum, nulla quo consequuntur numquam!</p>
        </div>
        </div>
        <div className='mt-12 text-center text-xl'>
            <p>For a more in-depth explaination, please click<span className="font-bold cursor-pointer" onClick={handleDownload}> here</span> for more information.</p>
        </div>
    </div>
  )
}

export default Vote