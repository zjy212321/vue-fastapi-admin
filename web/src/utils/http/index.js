import axios from 'axios'
import { resReject, resResolve, reqReject, reqResolve } from './interceptors'

export function createAxios(options = {}) {
  const defaultOptions = {
    timeout: 12000,
  }
  const service = axios.create({
    ...defaultOptions,
    ...options,
  })
  service.interceptors.request.use(reqResolve, reqReject)
  service.interceptors.response.use(resResolve, resReject)
  return service
}

export const request = createAxios({
  baseURL: import.meta.env.VITE_BASE_API,
})


// 添加文件上传接口
// export const uploadCaseFile = (formData) => {
//   return request.post('/api/upload', formData, {
//     headers: {
//       'Content-Type': 'multipart/form-data'
//     }
//   });
// };

// // 添加按键编号查询接口
// export const getCaseByKey = (keyNumber) => {
//   return request.get(`/api/get-by-key/${keyNumber}`);
// };