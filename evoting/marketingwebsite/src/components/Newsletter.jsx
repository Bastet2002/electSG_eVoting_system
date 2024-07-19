import React from 'react'

const Newsletter = () => {
  return (
    <div>
        <div className='w-full py-16 text-white px-4 mt-12 bg-red-500/80'>
            <div className='max-w-[1240px] mx-auto grid lg:grid-cols-3'> 
                <div className='lg:col-span-2 my-12'>
                <h1 className='md:text-3xl sm:text-2xl text-xl font-bold py-2'>Want to keep up with the latest news and updates?</h1>
                <p>Sign up to our newsletter today!</p>
            </div>
            <div className='my-4'>
                <div className='flex flex-col sm:flex-row items-center justify-between w-full'>
                    <input className='p-3 flex w-full rounded-md text-black' type="email" placeholder='Enter email:'></input>
                    <button className='bg-stone-200 text-red-500/80 rounded-md font-medium w-[200px] ml-4 my-6 px-6 py-3'>Notify Me!</button>
                </div>
            <p className='text-white'>We care about the protection of your data. Click <span className='font-bold'>here</span> to review our Privacy Policy</p>
            </div>
            </div>
        </div>
    </div>
  )
}

export default Newsletter