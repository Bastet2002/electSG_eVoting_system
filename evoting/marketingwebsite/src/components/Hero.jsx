import React from 'react'
import Background from "../assets/background_image.png"

const Hero = () => {
  return (
    <div id="/" className='w-full h-[90vh]' >
        <img src={Background} className='w-full h-full object-cover' />
        <div className='max-w-[1140px] m-auto'>
            <div className='absolute top-[40%] w-full md:[40%] max-w-[600px] h-full flex flex-col text-white p-8'>
                <h2 className='font-bold text-4xl'>Simple. Safe. Secure.Test</h2>
            </div>
        </div>`
    </div>
  )
}

export default Hero