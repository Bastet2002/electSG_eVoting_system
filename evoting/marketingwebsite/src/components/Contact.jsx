import React from 'react'
import Background_Profile from '../assets/background_profile.png'
import ProfilePic from '../assets/profilepic.png'
import { 
  FaFacebookF,
  FaTwitter,
  FaInstagram,
  FaLinkedin,
  FaLink,
} from 'react-icons/fa';

const Contact = () => {
  return (
    <div id="contact">
    <div className='py-4 text-2xl font-bold mt-16 mb-4 text-center'>Meet The Team</div>
      {/* Card Container */}
      <div className='flex justify-evenly flex-wrap'>
        {/* Card */}
        <div className='h-[500px] w-[290px] m-5 shadow-custom rounded-[10px] overflow-hidden text-center bg-stone-200'>
          {/* Card Background Image */}
          <div className='w-[100%] h-[230px] object-cover clip-path-custom'>
            <img src={Background_Profile}/>
          </div>
          {/* Card Profile Picture */}
          <div className='h-[120px] w-[120px] rounded-[50%] border-custom mt-[-90px] ml-20 relative'>
            <img src={ProfilePic}/>
          </div>
          {/* Card Information */}
          <div>
            <h3 className='text-xl p-[10px]'>Someone's name</h3>
            <p className='text-[13px] px-[10px] py-[20px]'>Lorem ipsum dolor sit amet, consectetur adipisicing elit. Ratione consequatur minus eum ea ex impedit suscipit libero molestias tenetur fuga!</p>
            {/* Card Icons */}
            <div className='flex text-[20px] no-underline text-red-500/80 px-24 py-0'>
              <FaFacebookF />
              <FaTwitter />
              <FaInstagram />
              <FaLinkedin />
            </div> 
          </div>
      </div>

      {/* Card Container */}
      <div className='flex justify-evenly flex-wrap'>
        {/* Card */}
        <div className='h-[500px] w-[290px] m-5  shadow-custom rounded-[10px] overflow-hidden text-center bg-stone-200'>
          {/* Card Background Image */}
          <div className='w-[100%] h-[230px] object-cover clip-path-custom'>
            <img src={Background_Profile}/>
          </div>
          {/* Card Profile Picture */}
          <div className='h-[120px] w-[120px] rounded-[50%] border-custom mt-[-90px] ml-20 relative'>
            <img src={ProfilePic}/>
          </div>
          {/* Card Information */}
          <div>
            <h3 className='text-xl p-[10px]'>Someone's name</h3>
            <p className='text-[13px] px-[10px] py-[20px]'>Lorem ipsum dolor sit amet, consectetur adipisicing elit. Ratione consequatur minus eum ea ex impedit suscipit libero molestias tenetur fuga!</p>
            {/* Card Icons */}
            <div className='flex text-[20px] no-underline text-red-500/80 px-24 py-0'>
              <FaFacebookF />
              <FaTwitter />
              <FaInstagram />
              <FaLinkedin />
            </div>
          </div>
        </div>
      </div>

      {/* Card Container */}
      <div className='flex justify-evenly flex-wrap'>
        {/* Card */}
        <div className='h-[500px] w-[290px] m-5  shadow-custom rounded-[10px] overflow-hidden text-center bg-stone-200'>
          {/* Card Background Image */}
          <div className='w-[100%] h-[230px] object-cover clip-path-custom'>
            <img src={Background_Profile}/>
          </div>
          {/* Card Profile Picture */}
          <div className='h-[120px] w-[120px] rounded-[50%] border-custom mt-[-90px] ml-20 relative'>
            <img src={ProfilePic}/>
          </div>
          {/* Card Information */}
          <div>
            <h3 className='text-xl p-[10px]'>Someone's name</h3>
            <p className='text-[13px] px-[10px] py-[20px]'>Lorem ipsum dolor sit amet, consectetur adipisicing elit. Ratione consequatur minus eum ea ex impedit suscipit libero molestias tenetur fuga!</p>
            {/* Card Icons */}
            <div className='flex text-[20px] no-underline text-red-500/80 px-24 py-0'>
              <FaFacebookF />
              <FaTwitter />
              <FaInstagram />
              <FaLinkedin />
            </div>
          </div>
        </div>
      </div>

      
      {/* Card Container */}
      <div className='flex justify-evenly flex-wrap'>
        {/* Card */}
        <div className='h-[500px] w-[290px] m-5  shadow-custom rounded-[10px] overflow-hidden text-center bg-stone-200'>
          {/* Card Background Image */}
          <div className='w-[100%] h-[230px] object-cover clip-path-custom'>
            <img src={Background_Profile}/>
          </div>
          {/* Card Profile Picture */}
          <div className='h-[120px] w-[120px] rounded-[50%] border-custom mt-[-90px] ml-20 relative'>
            <img src={ProfilePic}/>
          </div>
          {/* Card Information */}
          <div>
            <h3 className='text-xl p-[10px]'>Someone's name</h3>
            <p className='text-[13px] px-[10px] py-[20px]'>Lorem ipsum dolor sit amet, consectetur adipisicing elit. Ratione consequatur minus eum ea ex impedit suscipit libero molestias tenetur fuga!</p>
            {/* Card Icons */}
            <div className='flex text-[20px] no-underline text-red-500/80 px-24 py-0'>
              <FaFacebookF />
              <FaTwitter />
              <FaInstagram />
              <FaLinkedin />
            </div>
          </div>
        </div>
      </div>
      </div>

      {/* Card Container */}
      <div className='flex justify-evenly flex-wrap'>
        {/* Card */}
        <div className='h-[500px] w-[290px] m-5 shadow-custom rounded-[10px] overflow-hidden text-center bg-stone-200'>
          {/* Card Background Image */}
          <div className='w-[100%] h-[230px] object-cover clip-path-custom'>
            <img src={Background_Profile}/>
          </div>
          {/* Card Profile Picture */}
          <div className='h-[120px] w-[120px] rounded-[50%] border-custom mt-[-90px] ml-20 relative'>
            <img src={ProfilePic}/>
          </div>
          {/* Card Information */}
          <div>
            <h3 className='text-xl p-[10px]'>Someone's name</h3>
            <p className='text-[13px] px-[10px] py-[20px]'>Lorem ipsum dolor sit amet, consectetur adipisicing elit. Ratione consequatur minus eum ea ex impedit suscipit libero molestias tenetur fuga!</p>
            {/* Card Icons */}
            <div className='flex text-[20px] no-underline text-red-500/80 px-24 py-0'>
              <FaFacebookF />
              <FaTwitter />
              <FaInstagram />
              <FaLinkedin />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Contact