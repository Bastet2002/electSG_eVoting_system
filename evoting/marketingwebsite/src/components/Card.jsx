import React from 'react'

const Card = (props) => {
  return (
    <div>
        <div className=' bg-red-500/80 flex flex-col border text-left rounded-2xl py-12 px-8'>
            <div>
                <div className='bg-white inline-flex p-2 rounded-full'>
                    {props.icon}
                </div>
                <h3 className='text-white text-2xl font-bold py-4'>{props.heading}</h3>
                <p className='text-white'>
                    {props.text}
                </p>
                </div>
            </div>
    </div>
  )
}

export default Card